from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from notification.models import NotificationSetting


class ProfileEditView(UpdateView):
    model = NotificationSetting
    template_name = 'profile.html'
    # form_class = ProfileForm
    fields = ('style',)

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_object(self, queryset=None):
        """
        Get notification setting for the user.
        Create a new one if does not exists
        """
        try:
            ns = self.request.user.notification_setting
        except ObjectDoesNotExist:
            ns = NotificationSetting.objects.create(
                user=self.request.user
            )
        return ns
