from datetime import date
from celery import shared_task
from core.models.access import Access


@shared_task
def check_accesses_expiration():
    upper_date = date.today()
    Access.expire_accesses(upper_date)