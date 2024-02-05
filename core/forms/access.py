from django.forms import ModelForm, DateInput, Textarea
from core.forms import SkipFieldValidationMixin
from core.models import Access, Contact


class AccessForm(SkipFieldValidationMixin, ModelForm):
    class Meta:
        model = Access
        fields = "__all__"
        exclude = ["was_generated_automatically", "created_by", "history", "status"]
        widgets = {
            # Date pickers
            "granted_on": DateInput(attrs={"class": "datepicker"}),
            "grant_expires_on": DateInput(attrs={"class": "datepicker"}),
            # Textareas
            "access_notes": Textarea(attrs={"rows": 2, "cols": 40}),
        }
        heading = "Record Access"
        heading_help = (
            "Specify who can access the data and for how long. You can define access of each person or "
            "describe group of users with access in remarks below."
        )

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["defined_on_locations"].choices = [
            (d.id, d) for d in dataset.data_locations.all()
        ]
        # to improve form performance we directly select related contact types
        contact_queryset = Contact.objects.all().select_related("type")
        self.fields["contact"].queryset = contact_queryset

    field_order = [
        "contact",
        "user",
        "project",
        "defined_on_locations",
        "granted_on",
        "grant_expires_on",
        "access_notes",
    ]


class AccessEditForm(ModelForm):
    class Meta:
        model = Access
        fields = "__all__"
        exclude = ["created_by", "history"]
        widgets = {
            # Date pickers
            "granted_on": DateInput(attrs={"class": "datepicker"}),
            "grant_expires_on": DateInput(attrs={"class": "datepicker"}),
            # Textareas
            "access_notes": Textarea(attrs={"rows": 2, "cols": 40}),
        }

    field_order = [
        "contact",
        "user",
        "project",
        "defined_on_locations",
        "project",
        "granted_on",
        "grant_expires_on",
        "access_notes",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        self.fields["defined_on_locations"].choices = [
            (d.id, d) for d in kwargs["instance"].dataset.data_locations.all()
        ]
