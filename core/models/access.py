from datetime import datetime
from typing import List

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from enumchoicefield import EnumChoiceField, ChoiceEnum

from .utils import CoreModel
from model_utils import Choices


class StatusChoices(ChoiceEnum):
    precreated = "Pre-created"
    active = "Active"
    suspended = "Suspended"
    terminated = "Terminated"


class Access(CoreModel):
    """
    Represents the access given to an internal (LCSB) entity over data storage locations.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(user__isnull=False) & 
                    Q(contact__isnull=True)
                ) | (
                    Q(user__isnull=True) & 
                    Q(contact__isnull=False)
                ) | (
                    Q(user__isnull=True) & 
                    Q(contact__isnull=True)
                ),
                name='user_or_contact_only',
            )
        ]

    def clean(self):
        if self.user and self.contact:
            raise ValidationError("The Access is granted either to an User, or to a Contact. If you need both, please create two separate entries.")

    access_notes = models.TextField(null=False,
        blank=False,
        max_length=255,
        verbose_name='Remarks', 
        help_text='Remarks on why and how access was given, what is the purpose of use.'
    )

    contact = models.ForeignKey('core.Contact',
        verbose_name='Contact that has the access',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Use either `contact` or `user`'
    )

    created_by = models.ForeignKey('core.User',
        verbose_name='Created by',
        on_delete=models.CASCADE,
        help_text='Which User added this entry to DAISY',
        blank=True,
        null=True
    )

    dataset = models.ForeignKey('core.Dataset', 
        verbose_name='Dataset',
        related_name='accesses',
        on_delete=models.CASCADE,
        null=False,
        blank=False, 
        help_text='The dataset to which access is given.'
    )

    defined_on_locations = models.ManyToManyField('core.DataLocation',
        blank=True,
        related_name='accesses',
        verbose_name='Data Locations',
        help_text='The dataset locations on which access is defined.'
    )

    grant_expires_on = models.DateField(verbose_name='Grant expires on',
        blank=True,
        null=True, 
        help_text='The date on which data access will expire.'
    )

    granted_on = models.DateField(verbose_name='Granted on',
        blank=True,
        null=True, 
        help_text='The date on which data access was granted.'
    )

    project = models.ForeignKey(
        'core.Project',
        related_name='accesses_to_existing_datasets',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Project',  
        help_text='If the access was given in the scope of a particular Project please specify.'
    )

    status = EnumChoiceField(
        StatusChoices,
        blank=False,
        null=False,
        default=StatusChoices.precreated,
        help_text='The status of the Access'
    )

    user = models.ForeignKey('core.User', 
        related_name='user', 
        verbose_name='User that has the access',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Use either `contact` or `user`'
    )

    was_generated_automatically = models.BooleanField(
        verbose_name='Was created automatically',
        default=False,
        help_text='Was the entry generated automatically, e.g. by REMS?'
    )

    def __str__(self):
        if self.contact:
            return f'Access ({self.status}) to dataset {self.dataset.title} given to a user: {self.user}/{self.access_notes}'
        else:
            return f'Access ({self.status}) to dataset {self.dataset.title} given to a contact: {self.user}/{self.access_notes}'

    def delete(self, force:bool=False):
        self.status = StatusChoices.terminated
        self.save()
        if force:
            super().delete()


    @property
    def display_locations(self):
        return "\n".join([ str(loc) for loc in self.defined_on_locations.all()])

    @classmethod
    def find_for_user(cls, user) -> List[str]:
        accesses = cls.objects.filter(user=user, dataset__is_published=True)
        return cls._filter_expired(accesses)

    @classmethod
    def find_for_contact(cls, contact) -> List[str]:
        accesses = cls.objects.filter(contact=contact, dataset__is_published=True)
        return cls._filter_expired(accesses)
        
    @staticmethod
    def _filter_expired(accesses) -> List[str]:
        # For the performance reasons it does not use is active

        # The ones that are not expired yet
        non_expired_accesses = accesses.filter(grant_expires_on__gte=datetime.now(), status=StatusChoices.active)
        non_expired_accesses_names = [access.dataset.elu_accession for access in non_expired_accesses]

        # The ones that don't have the expiration date
        accesses_without_expiration = accesses.filter(grant_expires_on__isnull=True, status=StatusChoices.active)
        accesses_without_expiration_names = [access.dataset.elu_accession for access in accesses_without_expiration]

        # Remove the duplicates
        return list(set(non_expired_accesses_names + accesses_without_expiration_names))

    def is_active(self):
        if self.status != StatusChoices.active:
            return False

        if self.grant_expires_on != None and self.grant_expires_on < datetime.now():
            return False
        
        return True