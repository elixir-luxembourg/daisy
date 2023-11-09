import logging
import urllib

from django.views.generic import UpdateView, ListView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, reverse, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django import forms

from notification.models import Notification, NotificationSetting
from core.models import User

logger = logging.getLogger(__name__)


# Create your views here.
class NotificationSettingEditView(UpdateView):
    model = NotificationSetting
    template_name = "notification/notification_setting_edit.html"
    # form_class = ProfileForm
    fields = ("send_email", "send_in_app", "notification_offset")

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Notification settings updated"
        )
        return reverse_lazy("notifications_settings")

    def get_object(self, queryset=None):
        """
        Get notification setting for the user.
        Create a new one if does not exists
        """
        try:
            ns = self.request.user.notification_setting
        except ObjectDoesNotExist:
            ns = NotificationSetting.objects.create(user=self.request.user)
        return ns


class NotificationsListView(ListView):
    model = Notification
    template_name = "notification/notification_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["submit_url"] = reverse("notifications")
        context["show_dismissed"] = self.request.GET.get("show_dismissed") == "true"
        return context

    def get(self, request, *args, **kwargs):
        self.queryset = request.user.notifications.ordered()
        return super().get(request)


class NotificationAdminView(UserPassesTestMixin, NotificationsListView):
    class UserSelection(forms.Form):
        user = forms.ModelChoiceField(
            queryset=User.objects.all(), help_text="Select the user."
        )

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        if "pk" in self.kwargs:
            user = get_object_or_404(User, pk=self.kwargs["pk"])
            self.queryset = user.notifications.ordered()
        else:
            self.queryset = Notification.objects.all()
        return super().get_queryset()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["form"] = self.UserSelection(initial={})
        new_arguments = {
            "show_dismissed": self.request.GET.get("show_dismissed", "false"),
        }
        if "pk" in self.request.GET:
            user = get_object_or_404(User, pk=self.request.GET["pk"])
            new_arguments["pk"] = str(user.pk)
            context["recipient_filter"] = user.pk

        submit_url = reverse("notifications_admin")
        url_arguments = "?" + "&".join(
            [
                f"{urllib.parse.quote(key)}={urllib.parse.quote(value)}"
                for key, value in new_arguments.items()
            ]
        )
        context["submit_url"] = submit_url + url_arguments
        context["admin"] = True
        return context

    def post(self, request, **kwargs):
        form = self.UserSelection(request.POST)
        new_arguments = {"show_dismissed": request.GET.get("show_dismissed", "false")}
        if form.is_valid():
            user = form.cleaned_data.get("user")
            new_arguments["pk"] = str(user.pk)

        new_url = reverse("notifications_admin")
        url_arguments = "?" + "&".join(
            [
                f"{urllib.parse.quote(key)}={urllib.parse.quote(value)}"
                for key, value in new_arguments.items()
            ]
        )
        return redirect(new_url + url_arguments)
