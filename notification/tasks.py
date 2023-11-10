from datetime import datetime
import logging

from celery import shared_task

from notification import NotifyMixin

logger = logging.getLogger(__name__)


@shared_task
def create_notifications_for_entities(execution_date: str = None):
    """
    Loops through all the entities that implement the Notificaiton Mixin
    and creates notifications for each one of them according to the logic.

    Params:
        executation_date: The date of the execution of the task. FORMAT: YYYY-MM-DD (DEFAULT: Today)
    """
    if not execution_date:
        exec_date = datetime.now().date()
    else:
        exec_date = datetime.strptime(execution_date, "%Y-%m-%d").date()

    logger.info(f"Creating notifications for {exec_date}")

    for cls in NotifyMixin.__subclasses__():
        logger.info(f"Creating notifications for the {cls} entity...")
        cls.make_notifications(exec_date)
