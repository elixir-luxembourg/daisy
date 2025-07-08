from django import forms
from core.models import DAC, User, Dataset, Contract, Project


class DACForm(forms.ModelForm):
    projects = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="Project",
        help_text="Select a project to filter contracts.",
    )

    class Meta:
        model = DAC
        fields = [
            "title",
            "description",
            "projects",
            "contract",
            "local_custodians",
        ]
        heading = "Add new DAC"
        heading_help = "Provide basic information for the new dac."

    def __init__(self, *args, **kwargs):
        kwargs.pop("dac", None)
        contract_id = kwargs.pop("contract_id", None)
        super().__init__(*args, **kwargs)

        self.fields["local_custodians"].queryset = User.objects.exclude(
            username="AnonymousUser"
        )
        self.fields["contract"].choices = [
            (c.id, str(c)) for c in Contract.objects.all()
        ]

        # set initial contract and project if contract_id is provided
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                self.fields["contract"].initial = contract.id
                self.fields["contract"].choices = [(contract.id, str(contract))]
                project = contract.project
                if project:
                    self.fields["projects"].initial = project.id
                    self.fields["projects"].choices = [(project.id, str(project))]
                    self.fields["projects"].disabled = True
                    self.fields["contract"].disabled = True
            except Contract.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("projects")
        contract = cleaned_data.get("contract")

        # validate contract exists and belongs to project
        if contract and project:
            if contract.project != project:
                self.add_error(
                    "contract",
                    "Selected contract does not belong to the selected project.",
                )
        return cleaned_data


class DACFormEdit(DACForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["projects"].initial = kwargs["instance"].contract.project.id
        self.fields["projects"].disabled = True
        self.fields["contract"].disabled = True
        self.fields["title"].disabled = True
