from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.shortcuts import render, redirect
from web.views.utils import AjaxViewMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from sequences import get_next_value
from . import facet_view_utils
from core.models import User








class UsersListView(ListView):
    model = User
    template_name = 'users/user_list.html'

# class PartnerCreateView(CreateView, AjaxViewMixin):
#     model = User
#     template_name = 'partners/partner_form.html'
#     form_class =UserForm

# class UserEditView(UpdateView):
#     model = User
#     template_name = 'users/user_form_edit.html'


class UserDetailView(DetailView):
    model = User
    template_name = 'users/user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = True
        context['can_edit'] = can_edit
        return context

