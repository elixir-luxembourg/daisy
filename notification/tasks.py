from datetime import datetime
from collections import defaultdict
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from core.models import Contract, DataDeclaration, Dataset, Document, Project, User
from notification.email_sender import send_the_email
from notification.models import Notification, NotificationStyle, NotificationVerb
from notification import NotifyMixin

# map each notification style to a delta
# delta correspond to the interval + a small delta
NOTIFICATION_MAPPING = {
    NotificationStyle.once_per_day: timedelta(days=1, hours=8),
    NotificationStyle.once_per_week: timedelta(days=7, hours=16),
    NotificationStyle.once_per_month: timedelta(days=33),
}


@shared_task
def create_notifications_for_entities(executation_date: str = None):
    """
    Loops Through all the entitie that implement the Notificaiton Mixin
    and creates a notification for each one of them according to the logic.

    Params:
        executation_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
    """
    if not executation_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(executation_date, "%Y-%m-%d").date()

    for cls in NotifyMixin.__subclasses__():
        cls.make_notifications(exec_date)


# @shared_task
# def send_notifications_for_user_by_time(user_id, time):
#     """
#     Send a notification report for the current user from the date to the most recent.
#     """
#     # get latest notifications for the user, grouped by verb
#     notifications = Notification.objects.filter(actor__pk=user_id, time__gte=time)

#     if not notifications:
#         return

#     # group notifications per verb
#     notifications_by_verb = defaultdict(list)
#     for notif in notifications:
#         notifications_by_verb[notif.verb].append(notif)

#     user = User.objects.get(pk=user_id)
#     context = {"time": time, "user": user, "notifications": dict(notifications_by_verb)}
#     send_the_email(
#         settings.EMAIL_DONOTREPLY,
#         user.email,
#         "Notifications",
#         "notification/notification_report",
#         context,
#     )


# @shared_task
# def send_dataset_notification_for_user(user_id, dataset_id, created):
#     """
#     Send the notification that a dataset have been updated.
#     """
#     dataset = Dataset.objects.get(pk=dataset_id)
#     user = User.objects.get(pk=user_id)
#     context = {"user": user, "dataset": dataset, "created": created}
#     send_the_email(
#         settings.EMAIL_DONOTREPLY,
#         user.email,
#         "Notifications",
#         "notification/dataset_notification",
#         context,
#     )


# @shared_task
# def send_notifications(period):
#     """
#     Send notifications for each user based on the period selected.
#     Period must be one of `NotificationStyle` but 'every_time'.
#     """
#     notification_style = NotificationStyle[period]
#     if notification_style is NotificationStyle.every_time:
#         raise KeyError("Key not permitted")
#     # get users with this setting
#     users = User.objects.filter(
#         notification_setting__style=notification_style
#     ).distinct()
#     # map the setting to a timeperiod
#     now = timezone.now()
#     time = now - NOTIFICATION_MAPPING[notification_style]

#     # get latest notifications
#     users = users.filter(notifications__time__gte=time)
#     for user in users:
#         send_notifications_for_user_by_time.delay(user.id, time)
#     return users


# @shared_task
# def data_storage_expiry_notifications():
#     now = timezone.now()

#     # the user will receive notifications on two consecutive days prior to storage end date
#     window_2_start = now + datetime.timedelta(days=1)
#     window_2_end = now + datetime.timedelta(days=2)

#     # the user will receive notifications on two consecutive days, two months prior to storage end date
#     window_60_start = now + datetime.timedelta(days=59)
#     window_60_end = now + datetime.timedelta(days=60)

#     data_declarations = DataDeclaration.objects.filter(
#         Q(
#             end_of_storage_duration__gte=window_60_start,
#             end_of_storage_duration__lte=window_60_end,
#         )
#         | Q(
#             end_of_storage_duration__gte=window_2_start,
#             end_of_storage_duration__lte=window_2_end,
#         )
#     ).order_by("end_of_storage_duration")

#     for ddec in data_declarations:
#         for custodian in ddec.dataset.local_custodians.all():
#             Notification.objects.create(
#                 actor=custodian,
#                 verb=NotificationVerb.data_storage_expiry,
#                 content_object=ddec,
#             )


# @shared_task
# def document_expiry_notifications():
#     now = timezone.now()

#     # the user will receive notifications on two consecutive days prior to storage end date
#     window_2_start = now + datetime.timedelta(days=1)
#     window_2_end = now + datetime.timedelta(days=2)

#     # the user will receive notifications on two consecutive days, two months prior to storage end date
#     window_60_start = now + datetime.timedelta(days=59)
#     window_60_end = now + datetime.timedelta(days=60)

#     documents = Document.objects.filter(
#         Q(expiry_date__gte=window_60_start, expiry_date__lte=window_60_end)
#         | Q(expiry_date__gte=window_2_start, expiry_date__lte=window_2_end)
#     ).order_by("expiry_date")

#     for document in documents:
#         print(document.content_type)
#         if str(document.content_type) == "project":
#             obj = Project.objects.get(pk=document.object_id)
#         if str(document.content_type) == "contract":
#             obj = Contract.objects.get(pk=document.object_id)
#         if obj:
#             for custodian in obj.local_custodians.all():
#                 Notification.objects.create(
#                     actor=custodian,
#                     verb=NotificationVerb.document_expiry,
#                     content_object=obj,
#                 )
