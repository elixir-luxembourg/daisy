from django import forms
from django.shortcuts import get_object_or_404

from core.models import Dataset, User, Project
from core.models.contract import Contract


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['local_custodians', 'title']

    def __init__(self, *args, **kwargs):
        dataset = None
        if 'dataset' in kwargs:
            dataset = kwargs.pop('dataset')
        super().__init__(*args, **kwargs)
        self.fields['local_custodians'].queryset = User.objects.exclude(username='AnonymousUser')
        projects = Project.objects.filter().all()
        project_choices = [(None, "---------------------")]
        project_choices.extend([(p.id, str(p)) for p in projects])
        if dataset is not None and dataset.project:
            project_choices.append((dataset.project.id, str(dataset.project)))

        self.fields['project'] = forms.ChoiceField(choices=project_choices, required=False,
                                                   label       = Dataset.project.field.verbose_name,
                                                   help_text   = Dataset.project.field.help_text )

    def clean(self):
        """
        Validate the form:
        * One PI must be present in the responsible persons.
        """
        cleaned_data = super().clean()

        if not cleaned_data.get('project'):
            cleaned_data['project'] = None
        if 'local_custodians' not in cleaned_data:
            self.add_error('local_custodians', "You must specify Local Custodians for the dataset.")
        else:
            pis = cleaned_data.get('local_custodians').vips()
            if pis.first() is None:
                self.add_error('local_custodians', "Dataset\'s Local Custodians must include at least one PI.")
        return cleaned_data

    def save(self, commit=True):
        project_id = self.cleaned_data.get('project')
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            self.instance.project = project
        return super().save(commit)

    field_order = [
        'project',
        'local_custodians',
        'title'
    ]


class DatasetFormEdit(DatasetForm):

    class Meta(DatasetForm.Meta):
        fields = DatasetForm.Meta.fields +['other_external_id', 'sensitivity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].disabled = True



class ContractSelection(forms.Form):
    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop('dataset')
        super().__init__(*args, **kwargs)
        self.fields['contract'].queryset = Contract.objects.filter(
            memberships__project__memberships__dataset=self.dataset) | Contract.objects.filter(project=None)

    contract = forms.ModelChoiceField(queryset=Contract.objects.none())


class DatasetSelection(forms.Form):
    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop('dataset')
        super().__init__(*args, **kwargs)
        self.fields['dataset'].queryset = Dataset.objects.exclude(pk=self.dataset.pk)

    dataset = forms.ModelChoiceField(queryset=Dataset.objects.none())
