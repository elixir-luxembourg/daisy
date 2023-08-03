from django.forms import ModelForm

from core.forms.dataset import SkipFieldValidationMixin
from core.models import LegalBasis


class LegalBasisForm(SkipFieldValidationMixin,ModelForm):
    class Meta:
        model = LegalBasis
        fields = '__all__'
        exclude = []
        heading = "Data Legal Basis"
        heading_help = "Please provide a title for this data declaration"

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        if dataset:
            self.fields['data_declarations'].choices = [(d.id, d.title) for d in dataset.data_declarations.all()]

    field_order = [
        'data_declarations',
        'legal_basis_types',
        'personal_data_types',
        'remarks'
    ]


class LegalBasisEditForm(ModelForm):
    class Meta:
        model = LegalBasis
        fields = '__all__'
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in kwargs['instance'].dataset.data_declarations.all()]

