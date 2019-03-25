from django.forms import ModelForm, Textarea, Form, ChoiceField

from core.models import Publication


class PublicationForm(ModelForm):
    class Meta:
        model = Publication
        fields = '__all__'
        widgets = {
            'citation': Textarea(attrs={'max_length': '256'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        pass

    field_order = [
        'citation',
        'doi'
    ]


class PickPublicationForm(Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['publication'] = ChoiceField(choices=[(d.id, str(d)) for d in Publication.objects.all()])
