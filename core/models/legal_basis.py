from django.db import models

from .utils import CoreModel
from core import constants

class LegalBasis(CoreModel):
    """
    Holds the legal basis definition for a dataset.
    A Legal Basis definition may apply to an entire dataset (in this case data_declarations will be null).
    Or, a Legal Basis definition may apply to some data declarations within a dataset (data_declarations is not null).
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

        permissions = (
            (constants.Permissions.ADMIN.value, 'Can edit user permissions on LegalBasis instances'),
            (constants.Permissions.EDIT.value, 'Can edit the LegalBasis instances'),
            (constants.Permissions.DELETE.value, 'Can delete the LegalBasis instances'),
            (constants.Permissions.VIEW.value, 'Can view LegalBasis instances'),
            (constants.Permissions.PROTECTED.value, 'Can view/edit the protected elements of LegalBasis instances'),
        )

    dataset = models.ForeignKey('core.Dataset',
                                    related_name='legal_basis_definitions',
                                    on_delete=models.CASCADE
                                    )

    data_declarations = models.ManyToManyField('core.DataDeclaration',
                                                  blank=True,
                                                  related_name='processed_with_legal_bases',
                                                  verbose_name='Applies to',
                                                  help_text='The scope of this legal basis definition. Leave this field empty if the legal basis applies to entire dataset.')


    legal_basis_types = models.ManyToManyField("core.LegalBasisType",
                                                      blank=False,
                                                      related_name="legal_basis_definitions",
                                                      verbose_name='Legal Bases',  help_text='Under which legal bases for data processing, you can select more than one.')

    personal_data_types = models.ManyToManyField("core.PersonalDataType",
                                                  blank=True,
                                                  related_name="legal_basis_definitions",
                                                  verbose_name='Categories of personal data',  help_text='What categories of personal data is processed, you can select more than one.')

    remarks = models.TextField(null=True,
                                   blank=True,
                                   max_length=255,
                                   verbose_name='Remarks',
                                   help_text   = 'Justifications on why this legal basis is chosen.')


    def __str__(self):
        legal_basis_types = ",".join(str(lbt.code) for lbt in self.legal_basis_types.all())
        return f'Legal Basis for dataset {self.dataset.title}: {legal_basis_types}.'

    def to_dict(self):
        return {
            'legal_basis_codes': [x.code for x in self.legal_basis_types.all()],
            'personal_data_codes': [x.code for x in self.personal_data_types.all()],
            'legal_basis_notes': self.remarks if self.remarks else None,
            'data_declarations': [x.title for x in self.data_declarations.all()]
        }

    def serialize(self):
        result = self.to_dict()
        result['dataset'] = self.dataset.id
        return result
