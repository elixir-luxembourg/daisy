from django import forms

from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm

from core.models import Dataset, User
from core import constants


def generate_user_permission_form(permission_cls):
    """
    Generate user/permissions form based on a permission set
    """
    class UserPermForm(forms.Form):
        user = forms.ModelChoiceField(required=True, queryset=User.objects.exclude(username='AnonymousUser'))

        def __init__(self, *args, **kwargs):
            """
            Add permissions
            """
            super().__init__(*args, **kwargs)
            for perm in permission_cls:
                self.fields[perm.value] = forms.BooleanField(label=perm.name, required=False)

    return UserPermForm


# generate users/permissions formset based on the permissions available
# UserProjectPermFormSet = forms.formset_factory(
#     generate_user_permission_form(constants.Permissions), can_delete=True,  extra=1)

# UserDatasetPermFormSet = forms.formset_factory(
#     generate_user_permission_form(constants.Permissions), can_delete=True,  extra=1)

UserPermFormSet = forms.formset_factory(
    generate_user_permission_form(constants.Permissions), can_delete=True,  extra=1)