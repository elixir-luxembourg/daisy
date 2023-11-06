import smtplib
from collections import defaultdict
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from notification.email_sender import send_the_email
from notification.models import Notification
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def report_notifications_upcoming_events_errors_for_datasteward(user):
    """
    Send upcoming events notifications errors report for datasteward, if any.

    Params:
        user: The user whom the notifications sending failed
    """
    logger.info("Sending upcoming events notifications errors for datasteward")

    notifications_not_processed = Notification.objects.filter(
        recipient=user.id, dispatch_by_email=True, processing_date=None
    )

    # Send email to data steward in case of errors
    if notifications_not_processed:
        logger.error("Some notification are not processed: ")
        logger.error(notifications_not_processed)

        notifications_not_processed_by_content_type = defaultdict(list)

        for notif in notifications_not_processed:
            notifications_not_processed_by_content_type[notif.content_type].append(
                notif
            )

        context = {
            "notifications": dict(notifications_not_processed_by_content_type),
            "error_message": "Please find below the notifications that failed to be sent to user: "
            + user.full_name,
        }
        try:
            send_the_email(
                settings.EMAIL_DONOTREPLY,
                settings.DATASTEWARD_MAILING_LIST,
                "Notifications",
                "notification/email_datasteward_notifications_error",
                context,
            )
        except Exception as e:
            logger.error(
                f"Failed: An error occurred while sending Email notification error report for data-stewards."
                f" Error: {e}"
            )
            print(
                f"Failed: An error occurred while sending Email notification error report for data-stewards."
                f" Error: {e}"
            )


@shared_task
def send_notifications_for_user_upcoming_events(execution_date: str = None, only_one_day: bool = False):
    """
    Send upcoming events notification report for all users, if any.

    Params:
        execution_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
        only_one_day: If true send the notifications of the execution date only.
    """

    logger.info("Sending all notification for user upcoming events")

    if not execution_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(execution_date, "%Y-%m-%d").date()

    users = get_user_model().objects.all()

    for user in users:

        if only_one_day:
            notifications_exec_date = Notification.objects.filter(
                recipient=user.id,
                dispatch_by_email=True,
                processing_date=None,
                time__date=exec_date,
            )
        else:
            notifications_exec_date = Notification.objects.filter(
                recipient=user.id,
                dispatch_by_email=True,
                processing_date=None,
                time__date__lte=exec_date,
            )

        # send notification report to user, if any
        if not notifications_exec_date:
            # Checks if there is missed notification for this user and report errors to data-stewards, if any
            report_notifications_upcoming_events_errors_for_datasteward(user)
            continue

        # group notifications per content type and set processed to today
        notifications_by_content_type = defaultdict(list)
        for notif in notifications_exec_date:
            notifications_by_content_type[notif.content_type].append(notif)

        context = {
            "user": user.full_name,
            "notifications": dict(notifications_by_content_type),
        }

        try:
            send_the_email(
                settings.EMAIL_DONOTREPLY,
                user.email,
                "Notifications",
                "notification/email_list_notifications",
                context,
            )
            for notif in notifications_exec_date:
                notif.processing_date = datetime.now().date()
                notif.save()
        except Exception as e:
            logger.error(
                f"Failed: An error occurred while sending upcoming events Email notification for user {user.full_name}."
                f" Error: {e}"
            )
        finally:
            # report error to data-stewards
            report_notifications_upcoming_events_errors_for_datasteward(user)
            continue
