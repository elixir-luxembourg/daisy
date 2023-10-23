import json

from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from notification.models import Notification


@require_http_methods(["PATCH"])
def dismiss_notification(request, pk):
    notification = Notification.objects.get(pk)
    if request.user != notification.recipient:
        raise PermissionDenied(
            "You cannot dismiss a notification you are not the recipient of"
        )
    try:
        notification.dismissed = True
        notification.save()
    except Exception:
        return json.dumps({"success": False})

    return json.dumps({"success": True})
