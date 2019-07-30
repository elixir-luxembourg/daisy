from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from web.views.utils import AjaxViewMixin
from core.models import User
from core.forms.user import UserForm, UserEditForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin


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
    template_name = 'users/user_list.html'



@superuser_required()
class UserCreateView(CreateView, AjaxViewMixin):
    model = User
    template_name = 'users/user_form.html'
    form_class = UserForm
    success_message = 'New  user profile has been created'

    def form_valid(self, form):
        user = form.save(commit=False)
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user_permissions = form.cleaned_data['user_permissions']
        user.set_password(password)
        user.save()
        user.username = email
        user.source = settings.USER_SOURCE['manual']
        user.user_permissions.set(user_permissions)
        return super(UserCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users')


@superuser_required()
class UserEditView(UpdateView):
    model = User
    template_name = 'users/user_form_edit.html'
    form_class = UserEditForm
    success_message = 'User profile has been updated'

    def get_success_url(self):
        return reverse_lazy('user', kwargs={'pk': self.object.id})


@superuser_required()
class UserDetailView(DetailView):
    model = User
    template_name = 'users/user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = True
        context['can_edit'] = can_edit
        context['manual_source'] = settings.USER_SOURCE['manual']
        return context

@login_required
def change_password(request):
    if request.method == 'POST':
        print(request.POST)
        form = PasswordChangeForm(request.user, request.POST or None)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Important!
            messages.success(request, 'Your password was successfully updated! Please login again')
            return redirect('logout')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/user_change_password.html', {
        'form': form,

    })


class UserPasswordChange(PasswordChangeView):
    template_name = 'users/user_change_password.html'
    success_url = '/'

    def get_success_url(self):

        return reverse_lazy('login')


class UserDelete(DeleteView):
    model = User
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('users')
    success_message = "User was deleted successfully."

    def get_context_data(self, **kwargs):
        context = super(UserDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'user_delete'
        context['id'] = self.object.id
        return context
