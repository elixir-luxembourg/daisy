from datetime import date

from celery import shared_task
from django.core.management import call_command

from core.models.access import Access
from core.lcsb.rems import bulk_update_rems_external_ids


@shared_task
def check_accesses_expiration():
    """
    Task to expire accesses with a passed `grant_expiration_date` value
    """
    upper_date = date.today()
    Access.expire_accesses(upper_date)


@shared_task
def import_keycloak_users():
    """
    Create a DAISY user for every new Keycloak account, and update no stored row.
    match_keycloak_users runs once by hand, it is deliberately not scheduled.
    """
    call_command("import_keycloak_users")


@shared_task
def update_rems_access_external_id():
    """
    Task to update external id for REMS accesses
    """
    bulk_update_rems_external_ids()
