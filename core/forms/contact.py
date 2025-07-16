from django.forms import ModelForm, CharField, ChoiceField, Form, ValidationError

from core.models import Contact


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"
        exclude = ["oidc_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    field_order = [
        "first_name",
        "last_name",
        "type",
        "email",
        "partner",
        "address",
        "phone",
    ]

    def clean_oidc_id(self):
        # if the user is trying to change the oidc_id, raise an error
        if self.cleaned_data["oidc_id"]:
            raise ValidationError("You cannot set the OIDC ID of a contact.")


class PickContactForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"] = ChoiceField(
            label="Select contact",
            choices=[(d.id, str(d)) for d in Contact.objects.all()],
        )


class PickContactWithRemarkForm(Form):
    def __init__(self, *args, **kwargs):
        dac_pk = kwargs.pop("dac", None)
        super().__init__(*args, **kwargs)
        if dac_pk:
            contacts = Contact.objects.exclude(dacmembership__dac__id=dac_pk)
        else:
            contacts = Contact.objects.all()

        self.fields["contact"] = ChoiceField(
            label="Select contact",
            choices=[(None, "---------------------")]
            + [(d.id, str(d)) for d in contacts],
        )
        self.fields["remark"] = CharField(
            label="Remark",
            max_length=255,
            required=False,
            help_text="Optional remark for the contact.",
        )
