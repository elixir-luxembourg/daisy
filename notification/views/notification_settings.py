from django.views.generic.edit import UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist

from notification.models import NotificationSetting


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
