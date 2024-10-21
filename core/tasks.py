from datetime import date

from celery import shared_task

from core.models.access import Access
from core.lcsb.rems import synchronizer, bulk_update_rems_external_ids


@shared_task
def check_accesses_expiration():
    """
    Task to expire accesses with a passed `grant_expiration_date` value
    """
    upper_date = date.today()
    Access.expire_accesses(upper_date)


@shared_task
def run_synchronizer():
    """
    Task to synchronize users and contacts with the external system
    """
    synchronizer.synchronize_all()


@shared_task
def update_rems_access_external_id():
    """
    Task to update external id for REMS accesses
    """
    bulk_update_rems_external_ids()
