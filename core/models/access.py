from django.db import models

from .utils import CoreModel


class Access(CoreModel):
    """
    Represents the access given to an internal (LCSB) entity over data storage locations.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    access_notes = models.TextField(null=False,
                                    blank=False,
                                    max_length=255,
                                    verbose_name='Remarks', help_text='Remarks on why and how access was given, what is the purpose of use.' )

    granted_on = models.DateField(verbose_name='Granted on',
                                  blank=True,
                                  null=True, help_text='The date on which data access was granted.')

    grant_expires_on = models.DateField(verbose_name='Grant expires on',
                                        blank=True,
                                        null=True, help_text='The date on which data access will expire.')

    dataset = models.ForeignKey('core.Dataset',
                                verbose_name='Dataset',
                                related_name='accesses',
                                on_delete=models.CASCADE,
                                null=False,
                                blank=False, help_text='The dataset to which access is given.')

    defined_on_locations = models.ManyToManyField('core.DataLocation',
                                                  blank=False,
                                                  related_name='accesses',
                                                  verbose_name='Data Locations',  help_text='The dataset locations on which access is defined.')

    project = models.ForeignKey(
        'core.Project',
        related_name='accesses_to_existing_datasets',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Project',  help_text='If the access was given in the scope of a particular Project please specify.'
    )

    def __str__(self):
        return 'Access given to dataset {}: {}'.format(self.dataset.title, self.access_notes)

    @property
    def display_locations(self):
        return "\n".join(str(loc.cast().display) for loc in self.defined_on_locations.all())
