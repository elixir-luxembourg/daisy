from django import forms
from django.shortcuts import get_object_or_404


from core.models import DataDeclaration, Partner, Contract, GDPRRole
from core.models.contract import PartnerRole

from core.forms.use_restriction import UseRestrictionForm
class DataDeclarationDetailsForm(forms.ModelForm):
    class Meta:
        model = DataDeclaration
        fields = [
            'title',
            'cohorts',
            'comments',
            'data_types_generated',
            'data_types_received',
            'deidentification_method',
            'has_special_subjects',
            'subjects_category',
            'consent_status',
            'special_subjects_description',
            'end_of_storage_duration',
            'embargo_date',
            'data_types_notes'
        ]
        widgets = {
            # Date pickers
            'end_of_storage_duration': forms.DateInput(attrs={'class': 'datepicker'}),
            'embargo_date': forms.DateInput(attrs={'class': 'datepicker'}),
        }



RestrictionFormset = forms.formset_factory(UseRestrictionForm, extra=1, min_num=0, max_num=10)


class BaseDataDeclarationSubForm(forms.Form):
    def get_context(self):
        return {}

    def update(self, data_declaration):
        pass

    def after_save(self, data_declaration):
        pass

    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)


class DataDeclarationSubFormOther(BaseDataDeclarationSubForm):
    comment = forms.CharField(label="Please describe the source of this data", widget=forms.Textarea)

    def update(self, data_declaration):
        data_declaration.comments = self.cleaned_data['comment']


class DataDeclarationSubFormNew(BaseDataDeclarationSubForm):
    partner = forms.ChoiceField(label="Select repository or partner")
    contract = forms.ChoiceField(label="Select source contract", widget=forms.RadioSelect)

    # order of fields is important here, as clean_partner needs to be called before contract value validation
    # keep partner before contract

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner', None)
        super().__init__(*args, **kwargs)
        partners = list(Partner.objects.all())
        partners_choices = [(p.id, str(p)) for p in partners]
        if partners:
            if not partner:
                partner = partners[0]
            self.contracts = Contract.objects.filter(partners_roles__partner=partner,
                                                     local_custodians__in=self.dataset.local_custodians.all())
            contract_choices = [(c.id, str(c)) for c in self.contracts]
            self.fields['contract'].choices = contract_choices
        self.fields['partner'].choices = partners_choices

    def get_context(self):
        return {
            "contracts": self.contracts
        }

    def update(self, data_declaration):
        contract_id = int(self.cleaned_data['contract'])
        partner_id = int(self.cleaned_data['partner'])
        if contract_id:
            data_declaration.contract_id = contract_id
        else:
            # create new contract
            contract = Contract.objects.create()
            contract.project = data_declaration.dataset.project
            contract.save()
            contract.local_custodians.set(data_declaration.dataset.local_custodians.all())
            contract.company_roles.set([GDPRRole["processor"]])
            contract.save()
            partner_role = PartnerRole()
            partner_role.partner_id = partner_id
            partner_role.role = GDPRRole["controller"]
            partner_role.contract = contract
            partner_role.save()
            contract.partners_roles.set([partner_role])
            data_declaration.contract = contract
        data_declaration.partner_id = partner_id

    def after_save(self, data_declaration):
        contract_id = int(self.cleaned_data['contract'])
        if not contract_id:
            data_declaration.contract.local_custodians.set(data_declaration.dataset.local_custodians.all())

    def clean_partner(self):
        partner_id = int(self.cleaned_data['partner'])
        self.contracts = Contract.objects.filter(partners_roles__partner_id=partner_id,
                                                 local_custodians__in=self.dataset.local_custodians.all())
        contract_choices = [(c.id, str(c)) for c in self.contracts] + [(0, "new contract")]
        self.fields['contract'].choices = contract_choices
        return partner_id


class DataDeclarationSubFormFromExisting(BaseDataDeclarationSubForm):
    query = forms.CharField(label="Select origin data/samples", widget=forms.Select(choices=[]))

    def after_save(self, data_declaration):
        data_declaration_id = int(self.cleaned_data['query'])
        data_declaration_parent = get_object_or_404(DataDeclaration, id=data_declaration_id)
        data_declaration.copy(data_declaration_parent)
        data_declaration.data_declarations_parents.set([data_declaration_parent])
        data_declaration.save()


class DataDeclarationForm(forms.ModelForm):
    class Meta:
        model = DataDeclaration
        fields = ['title']

    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop('dataset')
        super().__init__(*args, **kwargs)
        type_choices = [
            (0, "From existing data/samples (from an LCSB collaborator or your own past project)"),
            (1, "Newly Incoming data/samples (from external collaborator/repository)"),
            (2, "Other (provenance unknown)")
        ]
        self.fields['type'] = forms.ChoiceField(label="Obtained from (choose one of the following)",
                                                choices=type_choices,
                                                widget=forms.RadioSelect())

    def clean(self):
        """
        Validate the form:
        * One PI must be present in the responsible persons.
        * samples_location field can be specified only when the "generated_from_samples" field is true #70
        """
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        self.instance.dataset = self.dataset
        return super().save(commit)

    field_order = [
        'title',
        'type',
    ]
