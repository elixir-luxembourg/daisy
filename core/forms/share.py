from django import forms
from django.forms import ModelForm, DateInput

from core.models import Share, Partner, Contract, PartnerRole


class ShareForm(ModelForm):
    class Meta:
        model = Share
        fields = '__all__'
        exclude = []
        widgets = {
            # Date pickers
            'granted_on': DateInput(attrs={'class': 'datepicker'}),
            'grant_expires_on': DateInput(attrs={'class': 'datepicker'})
        }
        help_texts = {
            'contract': ''
        }

    partner = forms.ModelChoiceField(
        queryset=Partner.objects.all(),
        widget=forms.Select(attrs={'id': 'partner-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset in this case shares have to be deleted and recreated
        self.fields.pop('dataset')

    field_order = [
        'partner',
        'contract',
        'data_declarations',
        'share_notes',
        'granted_on',
        'grant_expires_on'
    ]




class ShareFormEdit(ShareForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['partner'].disabled = True
        kwargs.pop('dataset', None)
        share_inst = kwargs.pop('instance', None)
        contracts = []
        partner_contracts = PartnerRole.objects.filter(partner=share_inst.partner)
        for pc in partner_contracts:
            contracts.append(pc.contract)
        if not contracts:
            self.fields[
                'contract'].help_text = 'No contract found with selected partner.'
        self.fields['contract'].choices = [(c.id, c.short_name()) for c in contracts]
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in share_inst.dataset.data_declarations.all()]


def shareFormFactory(*args, **kwargs):
    # model_form_class = Share
    initial = kwargs.pop('initial', {})
    partner = kwargs.pop('partner', None)
    if partner is not None:
        initial['partner'] = partner

    class ShareCreationForm(forms.ModelForm):

        class Meta:
            model = Share
            fields = '__all__'
            exclude = []
            widgets = {
                # Date pickers
                'granted_on': DateInput(attrs={'class': 'datepicker'}),
                'grant_expires_on': DateInput(attrs={'class': 'datepicker'})
            }

        partner = forms.ModelChoiceField(
            queryset=Partner.objects.all(),
            widget=forms.Select(attrs={'id': 'partner-select'})
        )

        field_order = [
            'partner',
            'contract',
            'share_notes',
            'granted_on',
            'grant_expires_on'
        ]

        def __init__(self, *args, **kwargs):
            self.dataset = kwargs.pop('dataset', None)
            super().__init__(*args, **kwargs)
            self.fields.pop('dataset')
            contracts = []
            if self.dataset.project and partner:
                contracts = Contract.objects.filter(partners_roles__partner=partner, project=self.dataset.project)
            if partner and contracts.count() == 0:
                self.fields[
                    'contract'].help_text = 'No contract found with selected partner.'

            self.fields['contract'].choices = [(c.id, c.short_name()) for c in contracts]
            self.fields['data_declarations'].choices = [(d.id, d.title) for d in self.dataset.data_declarations.all()]

    return ShareCreationForm(*args, **kwargs, initial=initial)
