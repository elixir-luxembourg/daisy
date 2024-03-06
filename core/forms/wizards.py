"""
Wizards forms
* select project
* select dataset
* select contract if any
"""
from django import forms

from core.models import Dataset, Contract, Project


class SelectProjectForm(forms.Form):
    class Meta:
        heading = "Select project"
        heading_help = "Select the project the dataset is attached to."

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), help_text="Select the project."
    )


class SelectDatasetForm(forms.Form):
    class Meta:
        heading = "Select dataset"
        heading_help = "Select the dataset associated with the project"

    dataset = forms.ModelChoiceField(queryset=Dataset.objects.all())
    is_owned = forms.BooleanField(
        label="Dataset is owned",
        required=False,
        help_text="Does the dataset is owned by the project ?",
    )


class SelectContractForm(forms.Form):
    class Meta:
        heading = "Select contract"
        heading_help = "Select the contract the project is using"

    contract = forms.ModelChoiceField(queryset=Contract.objects.all())
