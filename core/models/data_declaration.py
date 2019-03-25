import uuid

from django.db import models
from enumchoicefield import EnumChoiceField, ChoiceEnum

from core import constants
from core.models import DataType
from .utils import CoreModel, TextFieldWithInputWidget


class ConsentStatus(ChoiceEnum):
    unknown = "Unknown"
    heterogeneous = "Heterogeneous"
    homogeneous = "Homogeneous"


class DeidentificationMethod(ChoiceEnum):
    anonymization = 'anonymization'
    pseudonymization = 'pseudonymization'


class ShareCategory(ChoiceEnum):
    open_access = "open-access"
    controlled_access = "controlled-access"


class SubjectCategory(ChoiceEnum):
    unknown = "Unknown"
    cases = "Cases"
    controls = "Controls"
    cases_and_controls = "Cases and Controls"


class DataDeclaration(CoreModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = (
            (constants.Permissions.ADMIN.value, 'Responsible of the dataset'),
            (constants.Permissions.EDIT.value, 'Edit the dataset'),
            (constants.Permissions.DELETE.value, 'Delete the dataset'),
            (constants.Permissions.VIEW.value, 'View the dataset'),
            (constants.Permissions.PROTECTED.value, 'View the protected elements'),
        )

    partner = models.ForeignKey(
        "core.Partner",
        related_name="data_declarations",
        null=True,
        on_delete=models.SET_NULL,
        help_text='The Partner/Institute that have provided this data.'
    )

    contract = models.ForeignKey(
        "core.Contract",
        related_name="data_declarations",
        null=True,
        on_delete=models.SET_NULL,
        help_text='The Contract that ensures the legal receipt, keeping and analysis of this data.'
    )

    cohorts = models.ManyToManyField("core.Cohort", blank=True, related_name="data_declarations",  help_text='If the data is collected from subjects from a known/predefined Cohort please select it from the list.')

    comments = models.TextField(verbose_name='Other comments', blank=True, null=True, help_text='Pleae provide any remarks on the source and nature of data.')

    consent_status = EnumChoiceField(ConsentStatus, default=ConsentStatus.unknown, blank=False, null=False,
                                     help_text='Is the consent given by data subjects heterogeneous or homogeneous. Homogeneous consent  means that all subjects\' data have the same restrictions. Heterogeneous means that there are differences among consents given by subjects, therefore  there are differing use restrictions on data.')

    dataset = models.ForeignKey("core.Dataset", related_name="data_declarations", null=False, on_delete=models.CASCADE, help_text='The dataset that embodies this data.')

    data_types_generated = models.ManyToManyField("core.DataType",
                                                  blank=True,
                                                  related_name="data_declarations_generated",
                                                  verbose_name='Data types generated',  help_text='Select from the list the new types of data generated (if applicable).')
    data_types_received = models.ManyToManyField("core.DataType",
                                                 blank=True,
                                                 related_name="data_declarations_received",
                                                 verbose_name='Data types received', help_text='Select from the list the types of data received.')

    data_types_notes = models.TextField(verbose_name="Data types notes", blank=True, null=True, help_text='Remarks on data types, especially if dealing with a data type not present in the predefined list.')

    deidentification_method = EnumChoiceField(DeidentificationMethod, verbose_name='Deidentification method',
                                              default=DeidentificationMethod.pseudonymization, blank=False, null=False, help_text='How has the data been de-identified, is it pseudonymized or anonymized?')

    embargo_date = models.DateField(verbose_name='Embargo date',
                                    blank=True,
                                    null=True,
                                    help_text='If there is an embargo date associated with data, please specify it. Data cannot be published before the embargo date.')

    end_of_storage_duration = models.DateField(verbose_name='Storage end date', blank=True, null=True,
                                               help_text='Is the data obtained for a limited duration? If so please state the storage end date for data.')

    storage_duration_criteria = models.TextField(blank=True, null=True)

    has_special_subjects = models.NullBooleanField(null=True,
                                                   blank=True,
                                                   default=None,
                                                   verbose_name='Has special subjects?',
                                                   help_text='\"Special subjects\" refers to minors or those unable to give consent themselves e.g. advanced-stage dementia patients. If the data is collected from such subjects, please tick this box and provide an description.')

    other_external_id = TextFieldWithInputWidget(blank=True,
                                                 null=True,
                                                 verbose_name='Other Identifiers',
                                                 help_text='If the dataset has another external identifier such as accession number(s) or DOI(s), then please state them here.')

    share_category = EnumChoiceField(ShareCategory, verbose_name='Share category', blank=True, null=True)

    special_subjects_description = models.TextField(verbose_name='Description of special subjects',
                                                    blank=True,
                                                    help_text='This field should describe the nature of special data subjects (e.g. minors, elderly etc).',
                                                    null=True)

    subjects_category = EnumChoiceField(SubjectCategory,
                                        default=SubjectCategory.cases_and_controls,
                                        verbose_name='Subjects category', blank=False, null=False,
                                        help_text='This field designates if the data subjects are cases or controls or both.')

    submission_id = TextFieldWithInputWidget(
        verbose_name='Submission ID',
        null=True,
        help_text='This is the reference number in the submission portal. This field is only applicable for data submitted via the Submission Portal.',
        blank=True)

    title = TextFieldWithInputWidget(blank=False,
                                     max_length=255,
                                     verbose_name='Title', unique=True,
                                     help_text='Title is a brief description for the  data declaration. Think of how you - in the lab - refer to  data from a particular source; use that as the title.')

    unique_id = models.UUIDField(default=uuid.uuid4,
                                 editable=False,
                                 unique=True,
                                 blank=False,
                                 verbose_name='Unique identifier',
                                 help_text='This is the unique identifier used by DAISY for this dataset. This field annot be edited.')


    data_declarations_parents = models.ManyToManyField('core.DataDeclaration', verbose_name="", blank=True,
                                                       help_text='If this data declaration is based on or derived from an earlier declaration, then this field points to that ancestor/source declaration.',
                                                       related_name='data_declarations_derivated')

    def copy(self, source_data_declaration, excluded_fields=None, ignore_many_to_many=False):
        many_to_many_fields = [
            'data_types_received',
            'data_types_generated',
            'cohorts'
        ]
        if excluded_fields is None:
            excluded_fields = [
                'pk',
                'id',
                'added',
                'updated',
                'title',
                'unique_id',
                'other_external_id',
                'submission_id',
                'dataset_id'
            ]

        for key, value in source_data_declaration.__dict__.items():
            if key not in excluded_fields and not key.startswith('_'):
                setattr(self, key, value)
        if ignore_many_to_many:
            return

        for use_restriction in source_data_declaration.data_use_restrictions.all():
            clone_restriction = use_restriction.clone_shallow()
            clone_restriction.data_declaration = self
            self.data_use_restrictions.add(clone_restriction, bulk=False)

        for field in many_to_many_fields:
            if field not in excluded_fields:
                getattr(self, field).set(getattr(source_data_declaration, field).all())

    def __str__(self):
        return self.title

    @property
    def data_types(self):
        # return DataType.objects.filter(data_declarations_generated=self) | DataType.objects.filter(
        #     data_declarations_received=self)
        return set(DataType.objects.filter(data_declarations_generated=self).all()).union(
            set(DataType.objects.filter(data_declarations_received=self).all()))
