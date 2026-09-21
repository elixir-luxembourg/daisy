from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login, logout as dj_logout
from django.contrib.auth.decorators import login_required, login_not_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.conf import settings
from authlib.integrations.django_client import OAuth

from core.constants import Permissions
from core.forms.user import UserForm
from core.models import User
from core.models.project import ProjectUserObjectPermission
from core.models.dataset import DatasetUserObjectPermission
from core.models.user import UserSource
from core.synchronizers import get_contact
from core.utils import DaisyLogger, normalized_email
from web.views.utils import AjaxViewMixin

logger = DaisyLogger(__name__)


def superuser_required():
    def wrapper(wrapped):
        class WrappedClass(UserPassesTestMixin, wrapped):
            def test_func(self):
                return self.request.user.is_superuser

        return WrappedClass

    return wrapper


class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["oidc_enabled"] = getattr(settings, "OIDC_ENABLED", False)
        return context


@superuser_required()
class UsersListView(ListView):
    model = User
    template_name = "users/user_list.html"


@superuser_required()
class UserCreateView(CreateView, AjaxViewMixin):
    model = User
    template_name = "users/user_form.html"
    form_class = UserForm
    success_message = "New  user profile has been created"

    def form_valid(self, form):
        user = form.save(commit=False)
        email = form.cleaned_data["email"]
        groups = form.cleaned_data["groups"]
        user.set_unusable_password()
        user.username = email
        user.source = UserSource.MANUAL
        user.save()
        user.groups.set(groups)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("users")


@superuser_required()
class UserEditView(UpdateView):
    model = User
    template_name = "users/user_form_edit.html"
    success_message = "User profile has been updated"
    # every user is editable, whatever its source
    form_class = UserForm

    def get_success_url(self):
        return reverse_lazy("user", kwargs={"pk": self.object.id})


@superuser_required()
class UserDetailView(DetailView):
    model = User
    template_name = "users/user.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = True
        context["can_edit"] = can_edit
        project_set = ProjectUserObjectPermission.objects.filter(user=context["user"])
        dataset_set = DatasetUserObjectPermission.objects.filter(user=context["user"])
        project_perms = {}
        dataset_perms = {}
        for dsp in dataset_set:
            if "view" in dsp.permission.codename:
                continue
            if dsp.content_object in dataset_perms:
                dataset_perms[dsp.content_object].append(dsp.permission.codename)
            else:
                dataset_perms[dsp.content_object] = [dsp.permission.codename]
        for psp in project_set:
            if "view" in psp.permission.codename:
                continue
            if psp.content_object in project_perms:
                project_perms[psp.content_object].append(psp.permission.codename)
            else:
                project_perms[psp.content_object] = [psp.permission.codename]
        context["project_perms"] = project_perms
        context["dataset_perms"] = dataset_perms
        context["ds_perms_const"] = list(
            map(lambda x: f"{x}_dataset", [p.value for p in Permissions])
        )
        context["pj_perms_const"] = list(
            map(lambda x: f"{x}_project", [p.value for p in Permissions])
        )
        context["perms_const"] = list(Permissions)
        return context


@login_required
def change_password(request):
    if not request.user.has_usable_password():
        messages.error(request, "Your password is managed by Keycloak.")
        return redirect("dashboard")

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST or None)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Important!
            messages.success(
                request, "Your password was successfully updated! Please login again"
            )
            return redirect("logout")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(
        request,
        "users/user_change_password.html",
        {
            "form": form,
        },
    )


@superuser_required()
class UserDelete(DeleteView):
    model = User
    template_name = "../templates/generic_confirm_delete.html"
    success_url = reverse_lazy("users")
    success_message = "User was deleted successfully."

    def get_context_data(self, **kwargs):
        context = {}
        context["action_url"] = "user_delete"
        context["id"] = self.object.id
        return context


# OIDC authentication views
oauth = OAuth()
oauth.register("keycloak")


@login_not_required
def oidc_login(request):
    if not getattr(settings, "OIDC_ENABLED", False):
        messages.error(request, "OIDC authentication is not available.")
        return redirect("login")

    redirect_uri = request.build_absolute_uri(reverse("auth"))
    return oauth.keycloak.authorize_redirect(request, redirect_uri)


def _create_user(user_info, oidc_id, email):
    """
    The user of a first login: the username as Keycloak gives it, with the identity provider
    suffix or without, and an unusable password. The source stays the default, a login is not a
    directory import.
    """
    user = User(
        username=user_info.get("username"),
        email=email,
        first_name=user_info.get("given_name", ""),
        last_name=user_info.get("family_name", ""),
        oidc_id=oidc_id,
    )
    user.set_unusable_password()
    try:
        # a savepoint, a failed creation must not break the transaction of the caller
        with transaction.atomic():
            user.save()
    except IntegrityError as exception:
        # a concurrent first login won the race (select_for_update locks nothing when no row
        # matches), or an older DAISY row holds the username
        logger.error(exception)
        return User.objects.filter(oidc_id=oidc_id).first()
    return user


def _create_or_update_user(user_info, oidc_id, email):
    """
    The DAISY user of this Keycloak identity, created when DAISY does not hold it yet.
    None refuses the login: several active users share the email and nothing says which one is
    the person. Every identity provider may log in, the username suffix is a label only.
    """
    with transaction.atomic():
        user = User.objects.select_for_update().filter(oidc_id=oidc_id).first()
        if user:
            # TODO: requirement - an inactive user of this subject has to get a new account
            # instead of the refusal. It needs a decision first: oidc_id is unique and immutable
            # (User.save), so the subject has to move to the new row, and the access records, the
            # custodianships and the guardian permissions stay on the old one. The permissions
            # API answers by oidc_id and REMS recognises a granted entitlement by it
            # (check_existence_automatic), so both would stop seeing the older records
            return user

        contact = get_contact(oidc_id, email)
        if contact:
            # a contact never blocks a login, but its access rows need a migration
            logger.warning(
                f"Contact {contact.pk} holds the Keycloak subject {oidc_id} or its email, "
                f"the login creates a user and the access records of the contact stay behind"
            )

        # bind the record of this person, an inactive row is never adopted
        unbound = list(
            User.objects.select_for_update().filter(
                email__iexact=email, oidc_id__isnull=True, is_active=True
            )
        )
        if len(unbound) > 1:
            return None
        if unbound:
            user = unbound[0]
            user.oidc_id = oidc_id
            user.save(update_fields=["oidc_id"])
            return user

        return _create_user(user_info, oidc_id, email)


def _has_required_role(user_info) -> bool:
    """
    The client roles of DAISY, from the `resource_access` claim of the client that authenticated.
    An empty OIDC_REQUIRED_ROLE allows every account, as an instance without the role needs.
    """
    required_role = getattr(settings, "OIDC_REQUIRED_ROLE", "")
    if not required_role:
        return True
    client_roles = user_info.get("resource_access", {}).get(
        oauth.keycloak.client_id, {}
    )
    return required_role in client_roles.get("roles", [])


@login_not_required
def auth(request):
    try:
        token = oauth.keycloak.authorize_access_token(request)
    except Exception:
        messages.error(request, "Authentication failed.")
        return redirect("login")
    user_info = token.get("userinfo")

    if not user_info:
        messages.error(request, "Authentication failed.")
        return redirect("login")

    oidc_id = user_info.get("sub")
    email = normalized_email(user_info.get("email"))
    if not oidc_id or not email:
        messages.error(request, "Authentication failed.")
        return redirect("login")

    if not _has_required_role(user_info):
        # the identity is valid, the person may not use DAISY: nothing is created for them, and
        # the id_token stays for a logout of the Keycloak session
        if "id_token" in token:
            request.session["oidc_id_token"] = token["id_token"]
        messages.error(request, "Access not granted. Contact a data steward.")
        return redirect("login")

    user = _create_or_update_user(user_info, oidc_id, email)
    if not user:
        messages.error(
            request,
            "An account with this email already exists. Contact a data steward.",
        )
        return redirect("login")
    if not user.is_active:
        messages.error(request, "This account is inactive. Contact a data steward.")
        return redirect("login")

    request.session["user"] = user_info
    if "id_token" in token:
        request.session["oidc_id_token"] = token["id_token"]

    # django login
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, f"Welcome, {user.get_full_name() or user.username}!")
    return redirect("dashboard")


def logout(request):
    id_token = request.session.get("oidc_id_token")

    dj_logout(request)
    request.session.pop("user", None)
    request.session.pop("oidc_id_token", None)

    if id_token and getattr(settings, "OIDC_ENABLED", False):
        keycloak_logout_url = oauth.keycloak.server_metadata.get("end_session_endpoint")
        if keycloak_logout_url:
            redirect_uri = request.build_absolute_uri(reverse("login"))
            logout_url = f"{keycloak_logout_url}?post_logout_redirect_uri={redirect_uri}&id_token_hint={id_token}"
            return redirect(logout_url)

    return redirect("login")
