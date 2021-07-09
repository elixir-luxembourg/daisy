from datetime import datetime

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string
from enumchoicefield import EnumChoiceField
from enumchoicefield.enum import ChoiceEnum
from guardian.shortcuts import assign_perm, remove_perm

from core import constants
from core.models import Access, Dataset
from core.permissions import ProjectChecker, DatasetChecker, ContractChecker, AutoChecker
from .utils import TextFieldWithInputWidget


def create_api_key(length=48):
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return get_random_string(length, allowed_chars)

class UserSource(ChoiceEnum):
    ACTIVE_DIRECTORY = "active directory"
    MANUAL = "manual"


class UserQuerySet(models.QuerySet):
    def vips(self):
        return self.filter(groups__name=constants.Groups.VIP.value)

    def data_stewards(self):
        return self.filter(groups__name=constants.Groups.DATA_STEWARD.value)

    def auditors(self):
        return self.filter(groups__name=constants.Groups.AUDITOR.value)

    def legal_team(self):
        return self.filter(groups__name=constants.Groups.LEGAL.value)


class UserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def vips(self):
        return self.get_queryset().vips()

    def data_stewards(self):
        return self.get_queryset().data_stewards()

    def auditors(self):
        return self.get_queryset().auditors()

    def legal_team(self):
        return self.get_queryset().legal_team()

    def create_user(self, username, email, password=None, is_active=True, is_staff=False, is_admin=False):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(username,
                                email,
                                password=password,
                                )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    """
    Represents application user - real person, that can log in and have valid information coupled - like name or email.
    """

    class Meta:
        app_label = 'core'
        ordering = ['first_name', 'last_name']

    api_key = models.CharField(verbose_name='API key',
        blank=False,
        null=False,
        max_length=64,
        default=create_api_key,
        help_text='A token used to authenticate the user for accessing API'
    )
    email = models.EmailField(blank=False)
    full_name = TextFieldWithInputWidget(max_length=128)
    objects = UserManager()
    oidc_id = models.CharField(verbose_name='OIDC user identifier',
        blank=True,
        null=True,
        max_length=64,
        unique=True,
        help_text="Internal user identifier coming from OIDC's IdP"
    )
    source = EnumChoiceField(UserSource, default=UserSource.MANUAL, blank=False, null=False)

    

    def __str__(self):
        fullname = self.get_full_name()
        return fullname or self.username

    def save(self, *args, **kw):
        self.full_name = f'{self.first_name} {self.last_name}'
        super(User, self).save(*args, **kw)

    def is_part_of(self, *args):
        """
        Check if user is part of the group or goups given.
        """
        if len(args) == 1:
            return self.groups.filter(name=args[0]).exists()
        return self.groups.filter(name__in=args).exists()

    # Permission management
    # ======================================================================

    @staticmethod
    def _assign_perm(permission, user_object, permission_object):
        if not user_object.has_perm(permission, permission_object):
            assign_perm(permission, user_object, permission_object)

    @staticmethod
    def _remove_perm(permission, user_object, permission_object):
        if user_object.has_perm(permission, permission_object):
            remove_perm(permission, user_object, permission_object)

    def assign_permissions_to_dataset(self, dataset_object):
        if self.is_part_of(constants.Groups.VIP.value):
            self._assign_perm(constants.Permissions.PROTECTED.value, self, dataset_object)
            self._assign_perm(constants.Permissions.ADMIN.value, self, dataset_object)
        self._assign_perm(constants.Permissions.DELETE.value, self, dataset_object)
        self._assign_perm(constants.Permissions.EDIT.value, self, dataset_object)
        self._assign_perm(constants.Permissions.VIEW.value, self, dataset_object)

    def remove_permissions_to_dataset(self, dataset_object):
        self._remove_perm(constants.Permissions.ADMIN.value, self, dataset_object)
        self._remove_perm(constants.Permissions.DELETE.value, self, dataset_object)
        self._remove_perm(constants.Permissions.EDIT.value, self, dataset_object)
        self._remove_perm(constants.Permissions.VIEW.value, self, dataset_object)

    def assign_permissions_to_contract(self, contract):
        if self.is_part_of(constants.Groups.VIP.value):
            self._assign_perm(constants.Permissions.PROTECTED.value, self, contract)
            self._assign_perm(constants.Permissions.ADMIN.value, self, contract)
        self._assign_perm(constants.Permissions.DELETE.value, self, contract)
        self._assign_perm(constants.Permissions.EDIT.value, self, contract)
        self._assign_perm(constants.Permissions.VIEW.value, self, contract)

    def remove_permissions_to_contract(self, contract):
        self._remove_perm(constants.Permissions.ADMIN.value, self, contract)
        self._remove_perm(constants.Permissions.DELETE.value, self, contract)
        self._remove_perm(constants.Permissions.EDIT.value, self, contract)
        self._remove_perm(constants.Permissions.VIEW.value, self, contract)

    def assign_permissions_to_project(self, project_object):
        if self.is_part_of(constants.Groups.VIP.value):
            self._assign_perm(constants.Permissions.PROTECTED.value, self, project_object)
            self._assign_perm(constants.Permissions.ADMIN.value, self, project_object)
        self._assign_perm(constants.Permissions.DELETE.value, self, project_object)
        self._assign_perm(constants.Permissions.EDIT.value, self, project_object)
        self._assign_perm(constants.Permissions.VIEW.value, self, project_object)

    def remove_permissions_to_project(self, project_object):
        self._remove_perm(constants.Permissions.PROTECTED.value, self, project_object)
        self._remove_perm(constants.Permissions.ADMIN.value, self, project_object)
        self._remove_perm(constants.Permissions.DELETE.value, self, project_object)
        self._remove_perm(constants.Permissions.EDIT.value, self, project_object)
        self._remove_perm(constants.Permissions.VIEW.value, self, project_object)

    def is_admin_of_project(self, project_object):
        return ProjectChecker(self).check(constants.Permissions.ADMIN, project_object)

    def can_edit_project(self, project_object):
        return ProjectChecker(self).check(constants.Permissions.EDIT, project_object)

    def is_admin_of_dataset(self, dataset_object):
        return DatasetChecker(self).check(constants.Permissions.ADMIN, dataset_object)

    def can_edit_dataset(self, dataset_object):
        return DatasetChecker(self).check(constants.Permissions.EDIT, dataset_object)

    def has_permission_on_object(self, perm, obj):
        """
        Check if the user has the correct permission on the object.
        """
        return AutoChecker(self).check(perm, obj)

    def can_edit_contract(self, contract):
        """
        Check if user can edit a contract.
        True if he has ADMIN right on the project
        """
        return ContractChecker(self).check(constants.Permissions.EDIT, contract)

    def get_access_permissions(self):
        """
        Finds Accesses of the user, and returns a list of their dataset IDs 
        """
        accesses = Access.objects.filter(user=self, dataset__is_published=True)
        return [access.dataset.elu_accession for access in accesses]

    def add_rems_entitlement(self, 
        application: str, 
        resource: str, 
        user_id: str,
        email: str) -> bool:
        """
        Tries to find a dataset with `elu_accession` equal to `resource`.
        If it exists, it will add a new logbook entry (Access object) set to the current user
        Otherwise - it will raise an exception
        """
        notes = f'Set automatically by REMS application #{application}'
        dataset = Dataset.objects.get(elu_accession=resource)
        # TODO: Set created_by to REMS user
        # TODO: Add REMS user
        new_logbook_entry = Access(
            user=self,
            dataset=dataset,
            access_notes=notes,
            granted_on=datetime.now()
        )
        new_logbook_entry.save()
        return True

    @classmethod
    def find_user_by_email_or_oidc_id(cls, email, oidc_id, method):
        if method == 'email':
            return cls.objects.get(email=email)
        elif method == 'id':
            return cls.objects.get(oidc_id=oidc_id)
        elif method == 'auto':
            if cls.objects.filter(oidc_id=oidc_id).count() == 1:
                return cls.objects.get(oidc_id=oidc_id)
            if cls.objects.filter(email=email).count() == 1:
                return cls.objects.get(email=email)
            else:
                message = f'There are either zero, or 2 and more users with such `email` and `oidc_id`!'
                raise cls.DoesNotExist(message)
        else:
            raise KeyError('Wrong method! Only `id`, `email` and `auto` implemented!')
