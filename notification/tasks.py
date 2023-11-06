from datetime import datetime
from collections import defaultdict
from datetime import timedelta
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from core.models import Contract, DataDeclaration, Dataset, Document, Project, User
from notification.email_sender import send_the_email
from notification.models import Notification, NotificationStyle, NotificationVerb
from notification import NotifyMixin

logger = logging.getLogger(__name__)


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

    logger.info(f"Creating notifications for {exec_date}")

    for cls in NotifyMixin.__subclasses__():
        cls.make_notifications(exec_date)
