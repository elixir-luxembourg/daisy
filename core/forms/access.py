from django.forms import ModelForm, DateInput, ChoiceField

from core.models import Access, DataLocation


class AccessForm(ModelForm):
    class Meta:
        model = Access
        fields = '__all__'
        exclude = []
        widgets = {
            # Date pickers
            'granted_on': DateInput(attrs={'class': 'datepicker'}),
            'grant_expires_on': DateInput(attrs={'class': 'datepicker'})
        }

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['defined_on_locations'].choices = [(d.id, ' - '.join([str(d.category), str(d.backend), d.cast().display])) for d in dataset.data_locations.all()]


    field_order = [
        'defined_on_locations',
        'access_notes',
        'project',
        'granted_on'
        'grant_expires_on'
    ]



class AccessEditForm(ModelForm):
    class Meta:
        model = Access
        fields = '__all__'
        exclude = []
        widgets = {
            # Date pickers
            'granted_on': DateInput(attrs={'class': 'datepicker'}),
            'grant_expires_on': DateInput(attrs={'class': 'datepicker'})
        }

    field_order = [
        'defined_on_locations',
        'access_notes',
        'project',
        'granted_on'
        'grant_expires_on'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['defined_on_locations'].choices = [(d.id, ' - '.join([str(d.category), str(d.backend), d.cast().display])) for d in kwargs['instance'].dataset.data_locations.all()]

