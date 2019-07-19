from django.db import models

from .utils import CoreModel


class Share(CoreModel):
    """
    Represents the share of  dataset with an external (non-LCSB) entity.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    partner = models.ForeignKey('core.Partner',
                                verbose_name='Share partner',
                                related_name='shares',
                                null=True,
                                on_delete=models.SET_NULL,
                                blank=False,
                                help_text   = 'The Partner with which the data is shared.')

    share_notes = models.TextField(null=True,
                                    blank=True,
                                    max_length=255,
                                    verbose_name='Remarks',
                                   help_text   = 'Please state here the safeguards taken for the share, also any other remarks.')

    granted_on = models.DateField(verbose_name='Granted on',
                                  blank=True,
                                  null=True,
                                  help_text   = 'The date on which data sharing started.')

    grant_expires_on = models.DateField(verbose_name='Grant expires on',
                                  blank=True,
                                  null=True,
                                   help_text   = 'The date on which data sharing will be terminated.')

    dataset = models.ForeignKey('core.Dataset',
                              verbose_name='Dataset',
                              related_name='shares',
                              on_delete=models.CASCADE,
                              null=False,
                              blank=False,
                              help_text   = 'The dataset that has been shared.')


    data_declarations = models.ManyToManyField('core.DataDeclaration',
                                               blank=True,
                                               related_name='share_records',
                                               verbose_name='Scope of transfer',
                                               help_text='The scope of this transfer. Leave empty if the all data declarations were transferred.')

    contract = models.ForeignKey(
        'core.Contract',
        verbose_name='Contract',
        related_name='shares',
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        help_text   = 'The contract that provides the legal basis for this data share.'
    )

    def __str__(self):
        return 'Share/Transfer of {} with {}.'.format(self.dataset.title, self.partner.name)
