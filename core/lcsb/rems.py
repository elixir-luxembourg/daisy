import json
import urllib3

from datetime import datetime, date, timedelta
from dateutil.parser import isoparse
from typing import Dict, Union, Tuple

from django.conf import settings
from django.http import HttpRequest

from core.synchronizers import (
    DummyAccountSynchronizer,
    ExternalUserNotFoundException,
    InconsistentSynchronizerStateException,
    DummySynchronizationBackend,
)
from core.lcsb.oidc import (
    get_keycloak_config_from_settings,
    KeycloakSynchronizationBackend,
    KeycloakAccountSynchronizer,
)
from core.models.access import Access, StatusChoices
from core.models.contact import Contact
from core.models.dataset import Dataset
from core.models.user import User
from core.utils import DaisyLogger
from django.db.models import Q

logger = DaisyLogger(__name__)

if getattr(settings, "KEYCLOAK_INTEGRATION", False) is True:
    urllib3.disable_warnings()
    keycloak_config = get_keycloak_config_from_settings()
    keycloak_backend = KeycloakSynchronizationBackend(keycloak_config)
    synchronizer = KeycloakAccountSynchronizer(keycloak_backend)
else:
    dummy_backend = DummySynchronizationBackend()
    synchronizer = DummyAccountSynchronizer(dummy_backend)


def check_existence_automatic(item: Dict[str, str]) -> bool:
    """
    Checks if an active access automatically created for the same received data already exists
    """
    application, resource, user_oidc_id, email, expiration_date = extract_rems_data(
        item
    )
    filter_oidc = Q(user__oidc_id=user_oidc_id) | Q(contact__oidc_id=user_oidc_id)
    filter_resource_and_status = Q(
        dataset__elu_accession=resource,
        grant_expires_on=expiration_date,
        status=StatusChoices.active,
    )
    existing_accesses = Access.objects.filter(
        filter_resource_and_status & filter_oidc
    ).all()
    return any([a.was_generated_automatically for a in existing_accesses])


def handle_rems_callback(request: HttpRequest) -> bool:
    """
    Handles an entitlements request coming from REMS

    More information:
    https://rems2docs.rahtiapp.fi/configuration/#entitlements

    :returns: True if everything was processed, False if not
    """

    logger.debug("REMS :: Unpacking the data received from REMS...")
    body_unicode = request.body.decode("utf-8")

    try:
        request_post_data = json.loads(body_unicode)
    except:
        message = (
            f"REMS :: Received data in wrong format, because deserializing request"
            "s POST body failed!)!"
        )
        raise ValueError(message)

    if not isinstance(request_post_data, list):
        the_type = type(request_post_data)
        message = f'REMS :: Received data with wrong format (it is not a list, but "{the_type}" instead)!'
        raise TypeError(message)
    # check if accesses already exist for the received data and eventually update them
    # if all accesses already exist, return True and stop processing to avoid triggering again the synchronizer
    logger.debug(
        "REMS :: check if accesses automatically created already exists for the received data..."
    )
    already_existing_accesses = {
        index
        for index, item in enumerate(request_post_data)
        if check_existence_automatic(item)
    }
    if len(already_existing_accesses) == len(request_post_data):
        # all accesses already exist, stopping processing
        logger.debug("REMS :: all accesses already exists, noop, stopping processing.")
        return True

    logger.debug("REMS :: some accesses do not exist yet")
    statuses = [
        handle_rems_entitlement(item)
        for index, item in enumerate(request_post_data)
        if index not in already_existing_accesses
    ]
    return all(statuses)


def extract_rems_data(data: Dict[str, str]) -> Tuple[str, str, str, str, date]:
    """
    Extracts the data from the REMS request
    """
    application = data.get("application")
    resource = data.get("resource")
    user_oidc_id = data.get("user")
    email = data.get("mail")
    expiration_date = data.get("end")

    if expiration_date is None:
        expiration_date = build_default_expiration_date()
    else:
        expiration_date = isoparse(expiration_date).date()

    logger.debug(
        f"REMS :: * data access request id: {application}, user_oidc_id: {user_oidc_id}, user_email: {email}, resource: {resource}"
    )
    return application, resource, user_oidc_id, email, expiration_date


def build_default_expiration_date():
    return date.today() + timedelta(
        days=getattr(settings, "ACCESS_DEFAULT_EXPIRATION_DAYS", 90)
    )


def handle_rems_entitlement(data: Dict[str, str]) -> bool:
    """
    Handles a single piece of information about the entitlement from REMS.

    :returns: True if the user was found and the entitlement processed, False if not
    """
    application, resource, user_oidc_id, email, expiration_date = extract_rems_data(
        data
    )
    try:
        Dataset.objects.get(elu_accession=resource)
    except Dataset.DoesNotExist:
        message = f"REMS :: Dataset with such `elu_accession` ({resource}) does not exist! Quitting"
        logger.error(f" * {message}")
        # TODO: E2E: Save and display a notification to DataStewards
        raise ValueError(message)

    try:
        entity = synchronizer.retrieve_and_update_user_or_contact(
            oidc_id=user_oidc_id, email=email, create_contact_if_not_found=True
        )
    except ExternalUserNotFoundException as e:
        logger.error(
            f"REMS :: User not found in synchronizer for id '{user_oidc_id}'",
            exc_info=e,
        )
        return False
    except InconsistentSynchronizerStateException as e:
        logger.error(
            f"REMS :: Inconsistent synchronizer state for id '{user_oidc_id}' and email {email}",
            exc_info=e,
        )
        return False

    return create_rems_entitlement(entity, application, resource, expiration_date)


def create_rems_entitlement(
    obj: Union[Access, User], application: str, dataset_id: str, expiration_date: date
) -> bool:
    """
    Tries to find a dataset with `elu_accession` equal to `dataset_id`.
    If it exists, it will add a new logbook entry (Access object) set to the current user/contact
    Assumes that the Dataset exists, otherwise will throw an exception.
    """
    dataset = Dataset.objects.get(elu_accession=dataset_id)
    notes = build_access_notes_rems(application)
    system_rems_user = get_or_create_rems_user()

    if type(obj) == User:
        new_logbook_entry = Access(
            user=obj,
            dataset=dataset,
            access_notes=notes,
            granted_on=datetime.now(),
            was_generated_automatically=True,
            created_by=system_rems_user,
            status=StatusChoices.active,
            grant_expires_on=expiration_date,
        )
    elif type(obj) == Contact:
        new_logbook_entry = Access(
            contact=obj,
            dataset=dataset,
            access_notes=notes,
            granted_on=datetime.now(),
            was_generated_automatically=True,
            created_by=system_rems_user,
            status=StatusChoices.active,
            grant_expires_on=expiration_date,
        )
    else:
        klass = obj.__class__.__name__
        raise TypeError(
            f"Wrong type of the object - should be Contact or User, is: {klass} instead"
        )

    new_logbook_entry.save()
    return True


def build_access_notes_rems(application: str) -> str:
    """
    Build and return note to be attached to the access created from a REMS application
    """
    return f"Set automatically by REMS data access request #{application}"


def get_or_create_rems_user() -> User:
    """
    Check if rems system user already exists and either return it directly or create it and return it
    """
    system_rems_user = User.objects.filter(username="system::REMS")
    # The password is not a hash, therefore it is
    # not possible to log into this account
    if system_rems_user.count() == 0:
        system_rems_user = User.objects.create(
            username="system::REMS",
            first_name=":REMS:",
            last_name=":System Account:",
            password="this is an invalid hash",
            email="lcsb-sysadmins+REMS@uni.lu",
        )
    else:
        system_rems_user = system_rems_user.first()
    return system_rems_user
