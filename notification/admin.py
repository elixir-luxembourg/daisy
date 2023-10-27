from django.contrib import admin

from notification.models import Notification, NotificationSetting


class NotificationAdmin(admin.ModelAdmin):
    readonly_fields = ("processing_date",)


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationSetting)
