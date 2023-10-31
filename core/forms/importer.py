from django import forms


class ImportForm(forms.Form):
    file = forms.FileField(required=True, label="Choose File")
