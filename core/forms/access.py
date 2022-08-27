from django.forms import ModelForm, DateInput, ChoiceField, Textarea

from core.models import Access, DataLocation


class AccessForm(ModelForm):
    class Meta:
        model = Access
        fields = '__all__'
        exclude = ['was_generated_automatically', 'created_by']
        widgets = {
            # Date pickers
            'granted_on': DateInput(attrs={'class': 'datepicker'}),
            'grant_expires_on': DateInput(attrs={'class': 'datepicker'}),
            # Textareas
            'access_notes': Textarea(attrs={'rows': 2, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['defined_on_locations'].choices = [(d.id, d) for d in dataset.data_locations.all()]


    field_order = [
        'contact',
        'user',
        'project',
        'defined_on_locations',
        'granted_on'
        'grant_expires_on'
        'access_notes',
    ]



class AccessEditForm(ModelForm):
    class Meta:
        model = Access
        fields = '__all__'
        exclude = []
        widgets = {
            # Date pickers
            'granted_on': DateInput(attrs={'class': 'datepicker'}),
            'grant_expires_on': DateInput(attrs={'class': 'datepicker'}),
            # Textareas
            'access_notes': Textarea(attrs={'rows': 2, 'cols': 40}),
        }

    field_order = [
        'contact',
        'user',
        'project',
        'defined_on_locations',
        'project',
        'granted_on'
        'grant_expires_on'
        'access_notes',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['defined_on_locations'].choices = [(d.id, d) for d in kwargs['instance'].dataset.data_locations.all()]
