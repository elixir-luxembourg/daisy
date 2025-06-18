from django import forms
from django.forms import ModelForm, ModelChoiceField, Textarea
from django.utils.text import slugify

from core.forms.input import SelectWithModal
from core.models import Contract, Project, Dataset, PartnerRole


class ContractForm(ModelForm):
    class Meta:
        model = Contract
        fields = "__all__"
        exclude = ["partners_roles"]
        widgets = {
            "comments": Textarea(attrs={"rows": 2, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        show_project = kwargs.pop("show_project", True)
        super().__init__(*args, **kwargs)
        if show_project:
            self.fields["project"] = ModelChoiceField(
                queryset=Project.objects.all(),
                required=False,
                label=Contract.project.field.verbose_name,
                help_text=Contract.project.field.help_text,
            )
        else:
            del self.fields["project"]

    field_order = ["name", "project", "type", "legal_documents", "comments"]


class ContractFormEdit(ContractForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].disabled = False


class KVForm(forms.Form):
    key = forms.CharField(widget=forms.TextInput())
    value = forms.CharField(widget=forms.TextInput())

    def clean_key(self):
        data = self.cleaned_data["key"]
        return slugify(data)


class PartnerRoleForm(ModelForm):
    class Meta:
        model = PartnerRole
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract"].disabled = True
        self.fields["partner"].widget = SelectWithModal(
            url_name="partner_add",
            entity_name="partner",
            choices=self.fields["partner"].widget.choices,
        )
        self.fields["contacts"].widget = SelectWithModal(
            url_name="contact_add",
            entity_name="contact",
            choices=self.fields["contacts"].widget.choices,
            allow_multiple_selected=True,
        )

    field_order = ["contract", "partner", "roles", "contacts"]


class DatasetSelection(forms.Form):
    class Meta:
        heading = "Select dataset"
        heading_help = "Select the dataset."

    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all(), help_text="Select the dataset."
    )
