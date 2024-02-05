from django.forms import ModelForm

from core.forms import SkipFieldValidationMixin
from core.models import LegalBasis


class LegalBasisForm(SkipFieldValidationMixin, ModelForm):
    class Meta:
        model = LegalBasis
        fields = "__all__"
        exclude = []
        heading = "Add Legal Basis"
        heading_help = (
            "Capture the legal grounds for processing of this dataset under GDPR (personal data only). "
            "This can require support from your data stewards and data protection officer (DPO)."
        )

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["data_declarations"].choices = [
            (d.id, d.title) for d in dataset.data_declarations.all()
        ]

    field_order = [
        "data_declarations",
        "legal_basis_types",
        "personal_data_types",
        "remarks",
    ]


class LegalBasisEditForm(ModelForm):
    class Meta:
        model = LegalBasis
        fields = "__all__"
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["data_declarations"].choices = [
            (d.id, d.title) for d in kwargs["instance"].dataset.data_declarations.all()
        ]
