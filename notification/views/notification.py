import urllib

from django.views.generic.list import ListView
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin


from django import forms
from notification.models import Notification


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
            queryset=get_user_model().objects.all(), help_text="Select the user."
        )

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        if "pk" in self.kwargs:
            user = get_object_or_404(get_user_model(), pk=self.kwargs["pk"])
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
            user = get_object_or_404(get_user_model(), pk=self.request.GET["pk"])
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
