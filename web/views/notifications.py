from django.conf import settings
from django import forms
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.http import HttpResponse
from django.core.paginator import Paginator

from core.models import User


class UserSelection(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), help_text='Select the user.')


def index(request):
    per_page = request.GET.get('per_page', 25)
    page = request.GET.get('page', '1')
    notifications = request.user.notifications.ordered()
    paginator = Paginator(notifications, per_page)
    notifications = paginator.get_page(page)
    context = {
        'notifications': notifications
    }
    return render(request, 'notifications/list.html',context)



def admin(request, pk=None):
    if not request.user.is_staff:
        return redirect('notifications')

    if request.method == 'GET':
        user = None
        initial = {}
        notifications = None
        submit_url = reverse_lazy('notifications_admin')
        if pk is not None:
            user = get_object_or_404(User, pk=pk)
            initial['user'] = user
            per_page = request.GET.get('per_page', 25)
            page = request.GET.get('page', '1')
            notifications = user.notifications.ordered()
            paginator = Paginator(notifications, per_page)
            notifications = paginator.get_page(page)
            submit_url = reverse('notifications_admin_for_user', kwargs={'pk': user.pk})
        form = UserSelection(initial=initial)
        return render(request, 'notifications/list.html', {
            'form': form,
            'notifications': notifications,
            'submit_url': submit_url
        })
    if request.method == 'POST':
        form = UserSelection(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            return redirect('notifications_admin_for_user', pk = user.pk)