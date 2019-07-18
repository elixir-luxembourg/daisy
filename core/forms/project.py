from django import forms
from django.forms import ModelForm, DateInput, ValidationError
from django.urls import reverse_lazy

from core.models import Project, User, Dataset, DiseaseTerm, PhenotypeTerm
from core.models.term_model import TermCategory, GeneTerm, StudyTerm


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            # Date pickers
            'start_date': DateInput(attrs={'class': 'datepicker'}),
            'end_date': DateInput(attrs={'class': 'datepicker'}),
        }
        exclude = ['publications', 'contacts']

    field_order = [
        'acronym',
        'title',

        'legal_documents',
        'description',

        'start_date',
        'end_date',
        'local_custodians',
        'company_personnel',
        'study_terms',

        # Project
        'umbrella_project',
        'project_web_page',
        'disease_terms',
        'gene_terms',
        'phenotype_terms',
        'funding_sources',


        'has_cner',
        'cner_notes',
        'has_erp',
        'erp_notes',

        'includes_automated_profiling',

        'comments'
    ]

    def __init__(self, *args, **kwargs):
        kwargs['label_suffix'] = ""
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)

        if 'data' not in kwargs:
            #We do not want the entire Ontology Terms be rendered as options in the select. Hence the following:
            if instance is None:
            #Get - CREATE
                self.fields['disease_terms'].queryset = DiseaseTerm.objects.none()
                self.fields['phenotype_terms'].queryset = PhenotypeTerm.objects.none()
                self.fields['gene_terms'].queryset = GeneTerm.objects.none()
                self.fields['study_terms'].queryset = StudyTerm.objects.none()
            else:
            #Get - UPDATE
                self.fields['disease_terms'].queryset = instance.disease_terms.all()
                self.fields['phenotype_terms'].queryset = instance.phenotype_terms.all()
                self.fields['gene_terms'].queryset = instance.gene_terms.all()
                self.fields['study_terms'].queryset = instance.study_terms.all()

        self.fields['company_personnel'].queryset = User.objects.exclude(username='AnonymousUser')
        self.fields['local_custodians'].queryset = User.objects.exclude(username='AnonymousUser')

        self.fields['disease_terms'].widget.attrs['class'] = 'ontocomplete'+ ' '+ self.fields['disease_terms'].widget.attrs.get('class','')
        self.fields['disease_terms'].widget.attrs['data-url'] = reverse_lazy('api_termsearch', kwargs={'category': TermCategory.disease.value})

        self.fields['phenotype_terms'].widget.attrs['class'] = 'ontocomplete'+ ' '+ self.fields['phenotype_terms'].widget.attrs.get('class','')
        self.fields['phenotype_terms'].widget.attrs['data-url'] = reverse_lazy('api_termsearch', kwargs={'category': TermCategory.phenotype.value})

        self.fields['gene_terms'].widget.attrs['class'] = 'ontocomplete'+ ' '+ self.fields['gene_terms'].widget.attrs.get('class','')
        self.fields['gene_terms'].widget.attrs['data-url'] = reverse_lazy('api_termsearch', kwargs={'category': TermCategory.gene.value})

        self.fields['study_terms'].widget.attrs['class'] = 'ontocomplete'+ ' '+ self.fields['study_terms'].widget.attrs.get('class','')
        self.fields['study_terms'].widget.attrs['data-url'] = reverse_lazy('api_termsearch', kwargs={'category': TermCategory.study.value})


    def clean(self):
            """
            Override to check if at least one PI is in the responsibles people.
            """
            cleaned_data = super().clean()
            local_custodians = cleaned_data.get("local_custodians", [])
            if not local_custodians or not local_custodians.vips().exists():
                raise ValidationError(
                    "At least one PI must be in the responsible persons."
                )
            # validation for Ethics approval fields
            has_cner = cleaned_data.get('has_cner')
            has_erp = cleaned_data.get('has_erp')
            cner_notes = cleaned_data.get('cner_notes')
            erp_notes = cleaned_data.get('erp_notes')
            if not has_cner and not has_erp:
                if not cner_notes and not erp_notes:
                    self.add_error('cner_notes',  "Please enter notes on why there is no Institutional or National Ethics approval")
                    self.add_error('erp_notes',  "Please enter notes on why there is no Institutional or National Ethics approval")
            return self.cleaned_data


class DatasetSelection(forms.Form):
    class Meta:
        heading = 'Select dataset'
        heading_help = 'Select the the dataset the project uses.'

    dataset = forms.ModelChoiceField(queryset=Dataset.objects.all(), help_text='Select the dataset.')


