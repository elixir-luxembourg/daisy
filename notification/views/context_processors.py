from django.conf import settings


def daisy_notifications_enabled(request):
    notifications_enabled = not getattr(settings, "NOTIFICATIONS_DISABLED", True)
    return {"notifications_enabled": notifications_enabled}
