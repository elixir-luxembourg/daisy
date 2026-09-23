from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

from core.models import User


class UserForm(forms.ModelForm):
    """
    Create and edit a user, whatever its source. Keycloak is the only source of the accounts now,
    and the email has to stay editable: it is the key of the identity binding of a stored user.
    `is_active` is not here: a login activates the row again, so the field would promise a block
    it cannot hold. Disable the Keycloak account, or take the OIDC_REQUIRED_ROLE role away.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "groups"]

    field_order = [
        "first_name",
        "last_name",
        "email",
        "groups",
    ]


class PickUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["personnel"] = forms.ChoiceField(
            label="Select user",
            choices=[
                (d.id, str(d))
                for d in User.objects.exclude(username="AnonymousUser").all()
            ],
        )


class UserAuthForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "validate",
                "placeholder": settings.LOGIN_USERNAME_PLACEHOLDER,
                "autocomplete": "on",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": settings.LOGIN_PASSWORD_PLACEHOLDER,
                "autocomplete": "on",
            }
        )
    )
