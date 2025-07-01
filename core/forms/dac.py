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
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }
        heading = "Add new DAC"
        heading_help = "Provide basic information for the new dac."

    def __init__(self, *args, **kwargs):
        kwargs.pop("dac", None)
        dataset_id = kwargs.pop("dataset_id", None)
        contract_id = kwargs.pop("contract_id", None)
        super().__init__(*args, **kwargs)

        self.fields["local_custodians"].queryset = User.objects.exclude(
            username="AnonymousUser"
        )

        contract_choices = [(c.id, str(c)) for c in Contract.objects.all()]
        self.fields["contract"].choices = contract_choices

        # set only contracts related to the dataset if dataset_id is provided
        if dataset_id:
            dataset = get_object_or_404(Dataset, id=dataset_id)
            contract_choices = [(c.id, str(c)) for c in dataset.project.contracts.all()]
            self.fields["contract"].choices = contract_choices

        # set initial contract if contract_id is provided
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                self.fields["contract"].initial = contract.id
                self.fields["contract"].choices = [(contract.id, str(contract))]
            except Contract.DoesNotExist:
                pass

        self.fields_order = [
            "title",
            "description",
            "contract",
            "local_custodians",
        ]
        self.order_fields(self.fields_order)


class DACFormEdit(DACForm):
    pass
