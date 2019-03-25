from django import forms
from core.models import Document
from core.forms.input import CustomClearableFileInput


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'

        widgets = {
            'content': CustomClearableFileInput,
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        dropzone = kwargs.pop('dropzone', {})
        super().__init__(*args, **kwargs)


