from django.contrib import admin

from notification.models import Notification, NotificationSetting

admin.site.register(Notification)
admin.site.register(NotificationSetting)
