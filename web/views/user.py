from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required, login_not_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)
from authlib.integrations.django_client import OAuth

from core.constants import Permissions
from core.forms.user import UserForm, UserEditFormActiveDirectory, UserEditFormManual
from core.models import User
from core.models.project import ProjectUserObjectPermission
from core.models.dataset import DatasetUserObjectPermission
from core.models.user import UserSource
from web.views.utils import AjaxViewMixin


def superuser_required():
    def wrapper(wrapped):
        class WrappedClass(UserPassesTestMixin, wrapped):
            def test_func(self):
                return self.request.user.is_superuser

        return WrappedClass

    return wrapper


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
        password = form.cleaned_data["password"]
        groups = form.cleaned_data["groups"]
        user.set_password(password)
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

    def get_form_class(self):
        user = self.get_object()
        if user.source == UserSource.ACTIVE_DIRECTORY:
            return UserEditFormActiveDirectory
        else:
            return UserEditFormManual

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
        context["manual_source"] = UserSource.MANUAL
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


class UserPasswordChange(PasswordChangeView):
    template_name = "users/user_change_password.html"
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy("login")


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
    redirect_uri = request.build_absolute_uri(reverse("auth"))
    return oauth.keycloak.authorize_redirect(request, redirect_uri)


@login_not_required
def auth(request):
    token = oauth.keycloak.authorize_access_token(request)
    user_info = token.get("userinfo")
    request.session["user"] = user_info

    if not user_info:
        messages.error(request, "Authentication failed.")
        return redirect("login")

    oidc_id = user_info.get("sub")
    email = user_info.get("email")
    if not email:
        messages.error(request, "Authentication failed.")
        return redirect("login")

    try:
        user = User.objects.get(oidc_id=oidc_id)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=email)
            user.oidc_id = oidc_id
            user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=user_info.get("preferred_username", email),
                email=email,
            )
            user.first_name = user_info.get("given_name", "")
            user.last_name = user_info.get("family_name", "")
            user.oidc_id = oidc_id
            user.save()

    # django login
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, f"Welcome, {user.get_full_name() or user.username}!")
    return redirect("dashboard")
