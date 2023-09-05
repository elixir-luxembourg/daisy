from django import forms
from django.shortcuts import get_object_or_404
from django.forms import ValidationError
from core.models import Dataset, User, Project
from core.models.contract import Contract

from typing import Any


class SkipFieldValidationMixin:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the mixin. Adds a hidden Boolean field named `skip_wizard`
        to the form which determines if validation should be skipped.

        Args:
            *args: Variable arguments to pass to the superclass.
            **kwargs: Keyword arguments to pass to the superclass.
        """
        super().__init__(*args, **kwargs)
        self.fields["skip_wizard"] = forms.BooleanField(
            initial=False, required=False, widget=forms.HiddenInput()
        )

    def is_valid(self) -> bool:
        """
        Check if the form is valid. Validation is skipped if `skip_wizard` is True.

        Returns:
            bool: True if the form is valid or if `skip_wizard` is True, otherwise False.
        """
        if self.data.get(f"{self.prefix}-skip_wizard") == "True":
            return True
        return super().is_valid()


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ["local_custodians", "elu_accession", "title", "comments", "scientific_metadata"]
        exclude = ("is_published",)
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }
        heading = "Add new Dataset"
        heading_help = "Provide basic information for the new dataset."

    def __init__(self, *args, **kwargs):
        dataset = None
        if "dataset" in kwargs:
            dataset = kwargs.pop("dataset")
        super().__init__(*args, **kwargs)
        self.fields["local_custodians"].queryset = User.objects.exclude(
            username="AnonymousUser"
        )
        self.fields["elu_accession"].disabled = True
        projects = Project.objects.filter().all()
        project_choices = [(None, "---------------------")]
        project_choices.extend([(p.id, str(p)) for p in projects])

        self.fields["project"] = forms.ChoiceField(
            choices=project_choices,
            required=False,
            label=Dataset.project.field.verbose_name,
            help_text=Dataset.project.field.help_text,
        )
        self.fields_order = ["local_custodians", "title", "project", "comments"]
        self.order_fields(self.fields_order)

    def clean(self):
        """
        Validate the form:
        * One PI must be present in the responsible persons.
        """
        cleaned_data = super().clean()

        errors = []
        proj = cleaned_data["project"]
        if proj:
            project_inconsistency = False
            contracts = self.instance.collect_contracts()
            for contract, obj in contracts:
                if contract.project:
                    if str(contract.project.id) != proj:
                        project_inconsistency = True
                        error_msg = f"Dataset has existing link to Project {contract.project.acronym} via {obj}. Please remove link before updating this field."
                        self.add_error("project", error_msg)
            if project_inconsistency:
                errors.append("Unable to update project information.")

        local_custodians = cleaned_data.get("local_custodians", [])
        if not local_custodians or not local_custodians.vips().exists():
            errors.append("Local custodian information is missing or incomplete.")
            self.add_error(
                "local_custodians",
                "At least one PI must be in the responsible persons.",
            )

        if errors:
            raise ValidationError(errors)
        return cleaned_data

    def save(self, commit=True):
        project_id = self.cleaned_data.get("project")
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            self.instance.project = project
        else:
            self.instance.project = None
        return super().save(commit)


class DatasetFormEdit(DatasetForm):
    class Meta(DatasetForm.Meta):
        fields = DatasetForm.Meta.fields + ["other_external_id", "sensitivity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ContractSelection(forms.Form):
    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop("dataset")
        super().__init__(*args, **kwargs)
        self.fields["contract"].queryset = Contract.objects.filter(
            memberships__project__memberships__dataset=self.dataset
        ) | Contract.objects.filter(project=None)

    contract = forms.ModelChoiceField(queryset=Contract.objects.none())


class DatasetSelection(forms.Form):
    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop("dataset")
        super().__init__(*args, **kwargs)
        self.fields["dataset"].queryset = Dataset.objects.exclude(pk=self.dataset.pk)

    dataset = forms.ModelChoiceField(queryset=Dataset.objects.none())
