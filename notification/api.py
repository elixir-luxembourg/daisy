import json

from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

from notification.models import Notification


def jsonify(data):
    if isinstance(data, QuerySet):
        data = list(data)

    return json.dumps({"data": data})


@require_http_methods(["PATCH"])
def api_dismiss_notification(request, pk):
    notification = Notification.objects.get(pk)
    if request.user != notification.recipient:
        raise PermissionDenied(
            "You cannot dismiss a notification you are not the recipient of"
        )
    try:
        notification.dismissed = True
        notification.save()
    except Exception:
        return jsonify(False)

    return jsonify(True)


@require_http_methods(["GET"])
def api_get_notifications(request):
    notifications_list = Notification.objects.filter(
        recipient__pk=request.user.pk
    ).all()

    return jsonify(notifications_list)


@require_http_methods(["GET", "POST"])
def api_get_notifications_admin(request):
    if not request.user.is_staff:
        raise PermissionDenied("Only admin users can access this api endpoint")

    if request.method == "POST" and "pk" in request.POST:
        notifications_list = Notification.objects.filter(
            recipient__pk=request.POST["pk"]
        ).all()
    else:
        notifications_list = Notification.objects.all()

    return jsonify(notifications_list)
