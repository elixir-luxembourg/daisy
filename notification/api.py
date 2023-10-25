import json

from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import JsonResponse

from notification.models import Notification


def jsonify(data):
    if isinstance(data, QuerySet) or isinstance(data, list):
        data = [o.to_json() for o in data]
    else:
        data = data.to_json()

    return JsonResponse({"data": data}, status=200)


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
        return JsonResponse({"success": False})

    return JsonResponse({"success": True})


@require_http_methods(["GET"])
def api_get_notifications(request):
    notifications_list = Notification.objects.filter(
        dispatch_in_app=True,
    )

    if request.GET.get("show_dismissed") != "true":
        notifications_list = notifications_list.filter(dismissed=False)
    if request.GET.get("as_admin") != "true":
        notifications_list = notifications_list.filter(recipient__pk=request.user.pk)

    return jsonify(notifications_list.all())


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
