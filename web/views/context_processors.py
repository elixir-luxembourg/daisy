from importlib.metadata import version, PackageNotFoundError


def daisy_version(request):
    try:
        the_version = version("elixir-daisy")
    except PackageNotFoundError:
        the_version = "develop"
    except Exception:
        the_version = "develop"

    return {"app_version": the_version}


from django.conf import settings


def instance_branding(request):
    instance_label = getattr(settings, "INSTANCE_LABEL", None)
    instance_primary_color = getattr(settings, "INSTANCE_PRIMARY_COLOR", None)
    return {
        "instance_label": instance_label,
        "instance_primary_color": instance_primary_color,
    }
