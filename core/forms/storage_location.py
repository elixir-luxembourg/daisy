from django import forms

from core.forms import SkipFieldValidationMixin
from core.models import DataLocation


class StorageLocationForm(SkipFieldValidationMixin, forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = "__all__"
        exclude = []
        heading = "Add Storage Location"
        heading_help = (
            "Storage details ensure easy data retrieval and management. Record main location of the "
            "dataset. More storage locations can be added later."
        )

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["data_declarations"].choices = [
            (d.id, d.title) for d in dataset.data_declarations.all()
        ]

    field_order = [
        "category",
        "backend",
        "data_declarations",
        "datatypes",
        "location_description",
    ]


class StorageLocationEditForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = "__all__"
        exclude = []

    field_order = [
        "category",
        "backend",
        "data_declarations",
        "datatypes",
        "location_description",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["data_declarations"].choices = [
            (d.id, d.title) for d in kwargs["instance"].dataset.data_declarations.all()
        ]
