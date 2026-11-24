from django.forms import ModelChoiceField, ModelForm, ModelMultipleChoiceField
from django import forms
from core.models import Partner


def partner_label_from_instance(partner):
    if partner.acronym:
        return f"{partner.name} ({partner.acronym})"
    return partner.name


class PartnerChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return partner_label_from_instance(obj)


class PartnerMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return partner_label_from_instance(obj)


class PartnerForm(ModelForm):
    class Meta:
        model = Partner
        fields = "__all__"
        exclude = ["_is_published"]

        # widgets = {
        #     'elu_accession': forms.HiddenInput()
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["elu_accession"].disabled = True

    field_order = [
        "elu_accession",
        "acronym",
        "name",
        "address",
        "country",
        "geo_category",
        "sector_category",
        "is_clinical",
    ]


class PartnerFormEdit(PartnerForm):
    pass
