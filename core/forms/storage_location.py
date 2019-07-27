from django import forms
from core.models.storage_location import DataLocation


class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = '__all__'
        exclude = []

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in dataset.data_declarations.all()]

    field_order = [
        'category',
        'backend',
        'data_declarations',
        'datatypes',
        'location_description'
    ]

class StorageLocationEditForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = '__all__'
        exclude = []

    field_order = [
        'category',
        'backend',
        'data_declarations',
        'datatypes',
        'location_description'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in kwargs['instance'].dataset.data_declarations.all()]


