import json
import urllib3
from datetime import datetime, date, timedelta
from dateutil.parser import isoparse
from typing import Dict, Union, Tuple

from django.conf import settings
from django.http import HttpRequest
from django.db.models import Q
import requests

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
            "REMS :: Received data in wrong format, because deserializing request"
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


def extract_rems_data(data: Dict[str, str]) -> Tuple[int, str, str, str, date]:
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
    obj: Union[Access, User], application: int, dataset_id: str, expiration_date: date
) -> bool:
    """
    Tries to find a dataset with `elu_accession` equal to `dataset_id`.
    If it exists, it will add a new logbook entry (Access object) set to the current user/contact
    Assumes that the Dataset exists, otherwise will throw an exception.
    """
    dataset = Dataset.objects.get(elu_accession=dataset_id)
    external_id = get_rems_external_id(application)
    notes = build_access_notes_rems(application, external_id)
    system_rems_user = get_or_create_rems_user()

    access_kwargs = {
        "dataset": dataset,
        "access_notes": notes,
        "granted_on": datetime.now(),
        "was_generated_automatically": True,
        "created_by": system_rems_user,
        "status": StatusChoices.active,
        "grant_expires_on": expiration_date,
        "application_id": application,
        "application_external_id": external_id,
    }

    if isinstance(obj, User):
        new_logbook_entry = Access(user=obj, **access_kwargs)
    elif isinstance(obj, Contact):
        new_logbook_entry = Access(contact=obj, **access_kwargs)
    else:
        klass = obj.__class__.__name__
        raise TypeError(
            f"Wrong type of the object - should be Contact or User, is: {klass} instead"
        )

    new_logbook_entry.save()
    return True


def build_access_notes_rems(application: int, external_id: str) -> str:
    """
    Build and return note to be attached to the access created from a REMS application
    """
    result = f"Set automatically by REMS data access request #{application}"
    if external_id:
        result += f" ({external_id})"
    return result


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


def get_rems_application(application_id: int) -> dict:
    headers = {
        "x-rems-api-key": getattr(settings, "REMS_API_KEY"),
        "x-rems-user-id": getattr(settings, "REMS_API_USER"),
    }

    request_url = getattr(settings, "REMS_URL") + "api/applications"
    if application_id is not None:
        request_url = request_url + "/" + str(application_id)

    response = requests.get(
        request_url, headers=headers, verify=getattr(settings, "REMS_VERIFY_SSL")
    )
    response.raise_for_status()
    return json.loads(response.text)


def get_rems_external_id(application_id: int) -> str:
    attempt = 0
    max_retries = getattr(settings, "REMS_RETRIES")

    while attempt < max_retries:
        try:
            application_data = get_rems_application(application_id)
            return application_data.get("application/external-id")
        except Exception as e:
            attempt += 1
            logger.error(
                f"REMS :: Exception on requesting external ID for application {application_id}",
                exc_info=e,
            )
    return None


def bulk_update_rems_external_ids():
    accesses = Access.objects.filter(
        Q(application_external_id__isnull=True) & Q(application_id__isnull=False)
    )
    for access in accesses:
        external_id = get_rems_external_id(access.application_id)
        access.application_external_id = external_id
        access.access_notes = build_access_notes_rems(
            access.application_id, external_id
        )
    Access.objects.bulk_update(accesses, ["application_external_id", "access_notes"])
    logger.info(f"REMS :: Accesses updated: {len(accesses)}")
