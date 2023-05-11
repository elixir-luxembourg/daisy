from django import forms

from core.models import Endpoint


class EndpointEditForm(forms.ModelForm):
    class Meta:
        model = Endpoint
        fields = ["name", "url_pattern", "api_key"]
        widgets = {
            "api_key": forms.PasswordInput()
        }
