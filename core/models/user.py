from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from guardian.shortcuts import assign_perm, remove_perm

from core import constants
from core.permissions import ProjectChecker, DatasetChecker, ContractChecker, AutoChecker
from .utils import TextFieldWithInputWidget


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

    def create_user(self, username, email, password=None,is_active=True,is_staff=False,is_admin=False):
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

    email = models.EmailField(blank=False)
    source = models.CharField(max_length=128, blank=True, null=True,)
    full_name = TextFieldWithInputWidget(max_length=128)

    objects = UserManager()

    def __str__(self):
        fullname = self.get_full_name()
        return fullname or self.username

    def save(self, *args, **kw):
        self.full_name = '{0} {1}'.format(self.first_name, self.last_name)
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
