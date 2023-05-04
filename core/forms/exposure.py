import json

import requests
from django import forms
from django.conf import settings

from core.models import Exposure

class ExposureForm(forms.ModelForm):
    class Meta:
        model = Exposure
        fields = '__all__'
        exclude = ['created_by']

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        rems_forms_response = requests.get(getattr(settings, 'REMS_URL')+'api/forms',
                                           headers={"x-rems-api-key": getattr(settings, 'REMS_API_KEY'),
                                                    "x-rems-user-id": getattr(settings, 'REMS_API_USER')},
                                           verify=getattr(settings, 'REMS_VERIFY_SSL'))
        rems_forms_dict = json.loads(rems_forms_response.text)
        form_ids = []
        for rems_forms in rems_forms_dict:
            form_ids.append(rems_forms["form/id"])

        if not form_ids:
            form_ids.append(getattr(settings, 'REMS_FORM_ID'))

        self.fields['form_id'] = forms.ChoiceField(choices=[(i, i) for i in form_ids], widget=forms.Select)

    field_order = [
        'endpoint',
        'form_id'
    ]


class ExposureEditForm(forms.ModelForm):
    class Meta:
        model = Exposure
        fields = '__all__'
        exclude = ['created_by']

    field_order = [
        'endpoint',
        'form_id'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        rems_forms_response = requests.get(getattr(settings, 'REMS_URL')+'api/forms',
                                           headers={"x-rems-api-key": getattr(settings, 'REMS_API_KEY'),
                                                    "x-rems-user-id": getattr(settings, 'REMS_API_USER')},
                                           verify=getattr(settings, 'REMS_VERIFY_SSL'))
        rems_forms_dict = json.loads(rems_forms_response.text)
        form_ids = []
        for rems_forms in rems_forms_dict:
            form_ids.append(rems_forms["form/id"])
        if not form_ids:
            form_ids.append(getattr(settings, 'REMS_FORM_ID'))

        self.fields['form_id'] = forms.ChoiceField(choices=[(i, i) for i in form_ids], widget=forms.Select)

