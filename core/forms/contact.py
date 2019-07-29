from django.forms import ModelForm, ChoiceField, Form

from core.models import Contact


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    field_order = [
        'first_name',
        'last_name',
        'type',
        'email',
        'partner',
        'address',
        'phone'
    ]


class PickContactForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact'] = ChoiceField(label='Select contact', choices=[(d.id, str(d)) for d in Contact.objects.all()])
