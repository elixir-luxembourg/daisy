from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .utils import CoreModel


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

    user = models.ForeignKey('core.User', 
        related_name='user', 
        verbose_name='User with access',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Select either an User, or a Contact'
    )

    was_generated_automatically = models.BooleanField(
        verbose_name='Was created automatically',
        default=False,
        help_text='Was the entry generated automatically, e.g. by REMS?'
    )

    def __str__(self):
        return f'Access given to dataset {self.dataset.title}: {self.user}/{self.access_notes}'

    @property
    def display_locations(self):
        return "\n".join([ str(loc) for loc in self.defined_on_locations.all()])
