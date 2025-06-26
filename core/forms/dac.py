from django import forms
from django.shortcuts import get_object_or_404
from core.models import DAC, User, Dataset, Contact, Contract


class DACForm(forms.ModelForm):
    class Meta:
        model = DAC
        fields = [
            "title",
            "description",
            "contract",
            "local_custodians",
            "members",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }
        heading = "Add new DAC"
        heading_help = "Provide basic information for the new dac."

    def __init__(self, *args, **kwargs):
        kwargs.pop("dac", None)
        self.dataset_id = kwargs.get("initial", {}).get("dataset_id")
        super().__init__(*args, **kwargs)

        self.fields["local_custodians"].queryset = User.objects.exclude(
            username="AnonymousUser"
        )
        self.fields["members"].queryset = Contact.objects.all()

        contract_choices = [(c.id, str(c)) for c in Contract.objects.all()]
        self.fields["contract"].choices = contract_choices

        if self.dataset_id:
            dataset = get_object_or_404(Dataset, id=self.dataset_id)
            contract_choices = [(c.id, str(c)) for c in dataset.project.contracts.all()]
            self.fields["contract"].choices = contract_choices

        self.fields_order = [
            "title",
            "description",
            "contract",
            "local_custodians",
            "members",
        ]
        self.order_fields(self.fields_order)


class DACFormEdit(DACForm):
    pass
