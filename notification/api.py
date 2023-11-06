import logging

from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import JsonResponse

from notification.models import Notification


logger = logging.getLogger(__name__)


def jsonify(data):
    if isinstance(data, QuerySet) or isinstance(data, list):
        data = [o.to_json() for o in data]
    else:
        data = data.to_json()

    return JsonResponse({"data": data}, status=200)


@require_http_methods(["PATCH"])
def api_dismiss_notification(request, pk):
    notification = Notification.objects.get(pk=pk)
    if request.user != notification.recipient:
        raise PermissionDenied(
            "You cannot dismiss a notification you are not the recipient of"
        )
    logger.debug(f"Dismissing user {request.user.pk} notification {notification.pk}")
    notification.dismissed = True
    notification.save()

    notification_list = Notification.objects.filter(
        recipient=request.user, content_type=notification.content_type
    )
    return jsonify(notification_list)


@require_http_methods(["PATCH"])
def api_dismiss_all_notifications(request, object_type):
    notification_list = Notification.objects.filter(
        recipient=request.user, content_type__model=object_type
    )
    for notif in notification_list:
        notif.dismissed = True
        notif.save()

    logger.debug(
        f"Successfully dismissed {len(notification_list)} notifications for user {request.user.pk}"
    )
    return jsonify(notification_list)


@require_http_methods(["GET"])
def api_get_notifications(request):
    notifications_list = Notification.objects.filter(
        dispatch_in_app=True,
    )
    if request.GET.get("show_dismissed") != "true":
        notifications_list = notifications_list.filter(dismissed=False)
    if request.GET.get("as_admin") != "true":
        notifications_list = notifications_list.filter(recipient__pk=request.user.pk)
    elif request.GET.get("recipient", ""):
        notifications_list = notifications_list.filter(
            recipient__pk=request.GET.get("recipient")
        )

    breakpoint()
    return jsonify(notifications_list.all())


@require_http_methods(["GET"])
def api_get_notifications_number(request):
    number = Notification.objects.filter(
        recipient=request.user,
        dismissed=False,
        dispatch_in_app=True,
    ).count()

    return JsonResponse({"success": True, "data": number}, status=200)
