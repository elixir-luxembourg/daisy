from collections import defaultdict
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from notification.email_sender import send_the_email
from notification.models import Notification
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
def report_notifications_upcoming_events_errors_for_datasteward(
    execution_date: str = None,
):
    """
    Send upcoming events notifications errors report for datasteward, if any.

    Params:
        execution_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
    """
    logger.info("Sending upcoming events notifications errors for datasteward")

    if not execution_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(execution_date, "%Y-%m-%d").date()

    users = get_user_model().objects.all()

    for user in users:
        notifications_not_processed = Notification.objects.filter(
            recipient=user.id, dispatch_by_email=True, processing_date=None
        )
        notifications_exec_date = Notification.objects.filter(
            recipient=user.id,
            dispatch_by_email=True,
            processing_date=None,
            time__date=exec_date,
        )

        # Send email to data steward in case of errors
        if len(notifications_not_processed) != len(notifications_exec_date):
            # exclude execution date and today (in case task didn't run yet for today) notifications to get missed ones
            notifications_mismatch = notifications_not_processed.exclude(
                time__date=exec_date
            ).exclude(time__date=datetime.now().date())
            logger.error(
                "Notification mismatch between not processed and execution day notifications: "
            )
            logger.error(notifications_mismatch)
            notifications_mismatch_by_content_type = defaultdict(list)

            for notif in notifications_mismatch:
                notifications_mismatch_by_content_type[notif.content_type.model].append(
                    notif
                )

            context = {
                "notifications": dict(notifications_mismatch_by_content_type),
                "error_message": "Please find below the notifications mismatch between execution day "
                "notifications and not processed notifications for user: "
                + user.full_name,
            }
            send_the_email(
                settings.EMAIL_DONOTREPLY,
                settings.DATASTEWARD_MAILING_LIST,
                "Notifications",
                "notification/email_list_notifications",
                context,
            )


@shared_task
def send_notifications_for_user_upcoming_events(execution_date: str = None):
    """
    Send upcoming events notification report for all users, if any.

    Params:
        execution_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
    """

    logger.info("Sending notification for user upcoming events")

    if not execution_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(execution_date, "%Y-%m-%d").date()

    users = get_user_model().objects.all()

    for user in users:
        notifications_exec_date = Notification.objects.filter(
            recipient=user.id,
            dispatch_by_email=True,
            processing_date=None,
            time__date=exec_date,
        )

        # send notification report to user, if any
        if not notifications_exec_date:
            continue

        # group notifications per content type and set processed to today
        notifications_by_content_type = defaultdict(list)
        for notif in notifications_exec_date:
            notifications_by_content_type[notif.content_type.model].append(notif)
            notif.processing_date = datetime.now().date()
            notif.save()

        context = {
            "user": user.full_name,
            "notifications": dict(notifications_by_content_type),
        }
        send_the_email(
            settings.EMAIL_DONOTREPLY,
            user.email,
            "Notifications",
            "notification/email_list_notifications",
            context,
        )


@shared_task
def send_missed_notifications_for_user_upcoming_events(execution_date: str = None):
    """
    Send missed upcoming events notification report for all users, if any.

    Params:
        execution_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
    """

    logger.info("Sending missed notification for user upcoming events")

    if not execution_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(execution_date, "%Y-%m-%d").date()

    users = get_user_model().objects.all()

    for user in users:
        notifications_lte_exec_date = Notification.objects.filter(
            recipient=user.id,
            dispatch_by_email=True,
            processing_date=None,
            time__date__lte=exec_date,
        )

        # send notification report to user, if any
        if not notifications_lte_exec_date:
            continue

        # group notifications per content type and set processed to today
        notifications_by_content_type = defaultdict(list)
        for notif in notifications_lte_exec_date:
            notifications_by_content_type[notif.content_type.model].append(notif)
            notif.processing_date = datetime.now().date()
            notif.save()

        context = {
            "user": user.full_name,
            "notifications": dict(notifications_by_content_type),
        }
        send_the_email(
            settings.EMAIL_DONOTREPLY,
            user.email,
            "Notifications",
            "notification/email_list_notifications",
            context,
        )
