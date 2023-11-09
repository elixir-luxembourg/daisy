import pkg_resources

from django.conf import settings


def daisy_version(request):
    try:
        daisy_packages = pkg_resources.require("elixir-daisy")

        if len(daisy_packages) == 0:
            the_version = "develop"
        else:
            the_version = daisy_packages[0].version
    except:
        the_version = "develop"

    return {"app_version": the_version}


def daisy_notifications_enabled(request):
    notifications_enabled = not getattr(settings, "NOTIFICATIONS_DISABLED", True)
    return {"notifications_enabled": notifications_enabled}


def instance_branding(request):
    instance_label = getattr(settings, "INSTANCE_LABEL", None)
    instance_primary_color = getattr(settings, "INSTANCE_PRIMARY_COLOR", None)
    return {
        "instance_label": instance_label,
        "instance_primary_color": instance_primary_color,
    }
