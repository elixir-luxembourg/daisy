from django.forms import ModelForm
from django import forms
from core.models import Partner


class PartnerForm(ModelForm):
    class Meta:
        model = Partner
        fields = '__all__'
        widgets = {
            'elu_accession': forms.HiddenInput()
        }
        exclude = ['is_published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    field_order = [
        'elu_accession'
        'acronym',
        'name',
        'address',
        'country',
        'geo_category',
        'sector_category',
        'is_clinical',
        'is_published'
    ]


class PartnerFormEdit(PartnerForm):
    pass
