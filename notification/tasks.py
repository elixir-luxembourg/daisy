import datetime
from collections import defaultdict
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from core.models import Dataset, User
from notification.email_sender import send_the_email
from notification.models import (Notification, NotificationStyle)

# map each notification style to a delta
# delta correspond to the interval + a small delta
NOTIFICATION_MAPPING = {
    NotificationStyle.once_per_day: timedelta(days=1, hours=8),
    NotificationStyle.once_per_week: timedelta(days=7, hours=16),
    NotificationStyle.once_per_month: timedelta(days=33),
}


@shared_task
def send_notifications_for_user_by_time(user_id, time):
    """
    Send a notification report for the current user from the date to the most recent.
    """
    # get latest notifications for the user, grouped by verb
    notifications = Notification.objects.filter(
        actor__pk=user_id,
        time__gte=time
    )

    if not notifications:
        return

    # group notifications per verb
    notifications_by_verb = defaultdict(list)
    for notif in notifications:
        notifications_by_verb[notif.verb].append(notif)

    user = User.objects.get(pk=user_id)
    context = {
        'time': time,
        'user': user,
        'notifications': dict(notifications_by_verb)
    }
    send_the_email(
        settings.EMAIL_DONOTREPLY,
        user.email,
        'Notifications',
        'notification/notification_report',
        context,
    )


@shared_task
def send_dataset_notification_for_user(user_id, dataset_id, created):
    """
    Send the notification that a dataset have been updated.
    """
    dataset = Dataset.objects.get(pk=dataset_id)
    user = User.objects.get(pk=user_id)
    context = {
        'user': user,
        'dataset': dataset,
        'created': created
    }
    send_the_email(
        settings.EMAIL_DONOTREPLY,
        user.email,
        'Notifications',
        'notification/dataset_notification',
        context,
    )


@shared_task
def send_notifications(period):
    """
    Send notifications for each user based on the period selected.
    Period must be one of `NotificationStyle` but 'every_time'.
    """
    notification_style = NotificationStyle[period]
    if notification_style is NotificationStyle.every_time:
        raise KeyError('Key not permitted')
    # get users with this setting
    users = User.objects.filter(
        notification_setting__style=notification_style
    ).distinct()
    # map the setting to a timeperiod
    now = timezone.now()
    time = now - NOTIFICATION_MAPPING[notification_style]

    # get latest notifications
    users = users.filter(notifications__time__gte=time)
    for user in users:
        send_notifications_for_user_by_time.delay(user.id, time)
    return users



