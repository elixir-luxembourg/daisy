from django import forms
from core.models import Document
from core.forms.input import CustomClearableFileInput
from django.forms import DateInput


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'

        widgets = {
            'content': CustomClearableFileInput,
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
            'expiry_date': DateInput(attrs={'class': 'datepicker'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


