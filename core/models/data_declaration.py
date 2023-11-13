import uuid

from django.db import models
from django.urls import reverse
from enumchoicefield import EnumChoiceField, ChoiceEnum

from core import constants
from core.models import DataType
from .utils import CoreModel, TextFieldWithInputWidget


class ConsentStatus(ChoiceEnum):
    unknown = "Unknown"
    heterogeneous = "Heterogeneous"
    homogeneous = "Homogeneous"


class DeidentificationMethod(ChoiceEnum):
    anonymization = "anonymization"
    pseudonymization = "pseudonymization"


class ShareCategory(ChoiceEnum):
    open_access = "open-access"
    registered_access = "registered-access"
    controlled_access = "controlled-access"


class SubjectCategory(ChoiceEnum):
    unknown = "Unknown"
    cases = "Cases"
    controls = "Controls"
    cases_and_controls = "Cases and Controls"


class DataDeclaration(CoreModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        constraints = [
            models.UniqueConstraint(
                fields=["title", "dataset"], name="unique_title_dataset"
            )
        ]

    access_procedure = models.TextField(
        verbose_name="Remarks on the access procedure",
        blank=True,
        null=True,
        help_text='In case the access type is "open" or "controlled", you can elaborate on that',
    )

    contract = models.ForeignKey(
        "core.Contract",
        related_name="data_declarations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The Contract that ensures the legal receipt, keeping and analysis of this data.",
    )

    cohorts = models.ManyToManyField(
        "core.Cohort",
        blank=True,
        related_name="data_declarations",
        help_text="If the data is collected from subjects from a known/predefined Cohort please select it from the list.",
    )

    comments = models.TextField(
        verbose_name="Remarks on data source",
        blank=True,
        null=True,
        help_text="Please provide any remarks on the source and nature of data.",
    )

    consent_status = EnumChoiceField(
        ConsentStatus,
        default=ConsentStatus.unknown,
        blank=False,
        null=False,
        help_text="Is the consent given by data subjects heterogeneous or homogeneous. Homogeneous consent  means that all subjects' data have the same restrictions. Heterogeneous means that there are differences among consents given by subjects, therefore  there are differing use restrictions on data.",
    )

    dataset = models.ForeignKey(
        "core.Dataset",
        related_name="data_declarations",
        null=False,
        on_delete=models.CASCADE,
        help_text="The dataset that embodies this data.",
    )

    data_declarations_parents = models.ManyToManyField(
        "core.DataDeclaration",
        verbose_name="Derived/re-used from:",
        blank=True,
        help_text="If this data declaration is based on or derived from an earlier data declaration, then select ancestor data declaration.",
        related_name="data_declarations_derivated",
    )

    data_types_generated = models.ManyToManyField(
        "core.DataType",
        blank=True,
        related_name="data_declarations_generated",
        verbose_name="Data types generated",
        help_text="Select from the list the new types of data generated (if applicable).",
    )

    data_types_received = models.ManyToManyField(
        "core.DataType",
        blank=True,
        related_name="data_declarations_received",
        verbose_name="Data types received",
        help_text="Select from the list the types of data received.",
    )

    data_types_notes = models.TextField(
        verbose_name="Remarks on data types",
        blank=True,
        null=True,
        help_text="Remarks on data types, especially if dealing with a data type not present in the predefined list.",
    )

    deidentification_method = EnumChoiceField(
        DeidentificationMethod,
        verbose_name="Deidentification method",
        default=DeidentificationMethod.pseudonymization,
        blank=False,
        null=False,
        help_text="How has the data been de-identified, is it pseudonymized or anonymized?",
    )

    embargo_date = models.DateField(
        verbose_name="Embargo date",
        blank=True,
        null=True,
        help_text="If there is an embargo date associated with data, please specify it. Data cannot be published before the embargo date.",
    )

    end_of_storage_duration = models.DateField(
        verbose_name="Storage end date",
        blank=True,
        null=True,
        help_text="Is the data obtained for a limited duration? If so please state the storage end date for data.",
    )

    storage_duration_criteria = models.TextField(
        verbose_name="Storage duration criteria",
        blank=True,
        null=True,
        help_text="Please describe criteria used to determine storage duration.",
    )

    has_special_subjects = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Has special subjects?",
        help_text='"Special subjects" refers to minors or those unable to give consent themselves e.g. advanced-stage dementia patients. If the data is collected from such subjects, please tick this box and provide an description.',
    )

    other_external_id = TextFieldWithInputWidget(
        blank=True,
        null=True,
        verbose_name="Other Identifiers",
        help_text="If the dataset has another external identifier such as accession number(s) or DOI(s), then please state them here.",
    )

    partner = models.ForeignKey(
        "core.Partner",
        related_name="data_declarations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The Partner/Institute that have provided this data.",
    )

    share_category = EnumChoiceField(
        ShareCategory, verbose_name="Share category", blank=True, null=True
    )

    special_subjects_description = models.TextField(
        verbose_name="Description of special subjects",
        blank=True,
        help_text="This field should describe the nature of special data subjects (e.g. minors, elderly etc).",
        null=True,
    )

    subjects_category = EnumChoiceField(
        SubjectCategory,
        default=SubjectCategory.cases_and_controls,
        verbose_name="Subjects category",
        blank=False,
        null=False,
        help_text="This field designates if the data subjects are cases or controls or both.",
    )

    submission_id = TextFieldWithInputWidget(
        verbose_name="Submission ID",
        null=True,
        help_text="This is the reference number in the submission portal. This field is only applicable for data submitted via the Submission Portal.",
        blank=True,
    )

    title = TextFieldWithInputWidget(
        blank=False,
        max_length=255,
        verbose_name="Title",
        help_text="Title is a brief description for the  data declaration. Think of how you - in the lab - refer to  data from a particular source; use that as the title.",
    )

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        blank=False,
        verbose_name="Unique identifier",
        help_text="This is the unique identifier used by DAISY for this dataset. This field annot be edited.",
    )

    def get_absolute_url(self):
        return reverse("data_declaration", args=[str(self.pk)])

    def copy(
        self, source_data_declaration, excluded_fields=None, ignore_many_to_many=False
    ):
        many_to_many_fields = ["data_types_received", "data_types_generated", "cohorts"]
        if excluded_fields is None:
            excluded_fields = [
                "pk",
                "id",
                "added",
                "updated",
                "title",
                "unique_id",
                "other_external_id",
                "submission_id",
                "dataset_id",
            ]

        for key, value in source_data_declaration.__dict__.items():
            if key not in excluded_fields and not key.startswith("_"):
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

    def get_long_name(self):
        lname = self.title + " Dataset: " + self.dataset.title + ", Project: "
        if self.dataset.project is not None and self.dataset.project.title is not None:
            lname += self.dataset.project.title
        else:
            lname += "-"
        return lname

    def to_dict(self):
        use_restrictions_list = []
        for restriction in self.data_use_restrictions.all():
            use_restrictions_list.append(restriction.to_dict())

        cohort_short_dicts = []
        for cohort in self.cohorts.all():
            cohort_short_dicts.append(
                {
                    "cohort": cohort.title if cohort.title else None,
                    "cohort_external_id": cohort.elu_accession,
                }
            )

        base_dict = {
            "title": self.title,
            "cohorts": cohort_short_dicts,
            "data_types": [dt.name for dt in list(self.data_types)],
            "data_types_notes": self.data_types_notes
            if self.data_types_notes
            else None,
            "access_category": self.share_category.name
            if self.share_category
            else None,
            "access_procedure": self.access_procedure
            if self.access_procedure
            else None,
            "subjects_category": self.subjects_category.name
            if self.subjects_category
            else None,
            "de_identification": self.deidentification_method.name
            if self.deidentification_method
            else None,
            "consent_status": self.consent_status.name if self.consent_status else None,
            "has_special_subjects": self.has_special_subjects,
            "special_subjects_description": self.special_subjects_description,
            "embargo_date": self.embargo_date.strftime("%Y-%m-%d")
            if self.embargo_date
            else None,
            "storage_end_date": self.end_of_storage_duration.strftime("%Y-%m-%d")
            if self.end_of_storage_duration
            else None,
            "storage_duration_criteria": self.storage_duration_criteria
            if self.storage_duration_criteria
            else None,
            "use_restrictions": use_restrictions_list,
        }

        return base_dict

    @property
    def data_types(self):
        return set(
            DataType.objects.filter(data_declarations_generated=self).all()
        ).union(set(DataType.objects.filter(data_declarations_received=self).all()))

    def publish_subentities(self):
        if self.partner:
            self.partner.publish()

        for cohort in self.cohorts.all():
            cohort.publish()
