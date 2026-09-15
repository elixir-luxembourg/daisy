from datetime import date

from celery import shared_task
from django.core.management import call_command

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
def sync_keycloak_users():
    """
    Task to bind the oidc_id of the DAISY users and to deactivate the accounts that Keycloak
    does not know any more. Never with --deactivate-unmatched: an imported user waits without
    an oidc_id until the first login, and the flag would deactivate it every night.
    """
    call_command("sync_keycloak_users")


@shared_task
def update_rems_access_external_id():
    """
    Task to update external id for REMS accesses
    """
    bulk_update_rems_external_ids()
