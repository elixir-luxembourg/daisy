import json
import logging
import urllib3

from datetime import datetime
from typing import Dict, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from core.synchronizers import DummyAccountSynchronizer
from core.lcsb.oidc import get_keycloak_config_from_settings, KeycloakSynchronizationMethod, CachedKeycloakAccountSynchronizer
from core.models.access import Access
from core.models.contact import Contact
from core.models.dataset import Dataset
from core.models.user import User
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)


if getattr(settings, 'KEYCLOAK_INTEGRATION', False) == True:
    urllib3.disable_warnings()
    keycloak_config = get_keycloak_config_from_settings()
    keycloak_backend = KeycloakSynchronizationMethod(keycloak_config)
    synchronizer = CachedKeycloakAccountSynchronizer(keycloak_backend)
else:
    synchronizer = DummyAccountSynchronizer()


def handle_rems_callback(request: HttpRequest) -> bool:
    """
    Handles an entitlements request coming from REMS

    More information:
    https://rems2docs.rahtiapp.fi/configuration/#entitlements

    :returns: True if everything was processed, False if not
    """

    # Ensure the most recent account inforrmation by pulling it from Keycloak
    logger.debug('REMS :: Requesting refreshing the account information from Keycloak Synchronizer...')
    synchronizer.synchronize()
    logger.debug('REMS :: ...assuming that the OIDC account information has been synchronized')

    logger.debug('REMS :: Unpacking the data received from REMS...')
    body_unicode = request.body.decode('utf-8')

    try:
        request_post_data = json.loads(body_unicode)
    except:
        message = f'REMS :: Received data in wrong format, because deserializing request''s POST body failed!)!'
        raise ValueError(message)

    if not isinstance(request_post_data, list):
        the_type = type(request_post_data)
        message = f'REMS :: Received data with wrong format (it is not a list, but "{the_type}" instead)!'
        raise TypeError(message)

    statuses = [handle_rems_entitlement(item) for item in request_post_data]
    return all(statuses)

def handle_rems_entitlement(data: Dict[str, str]) -> bool:
    """
    Handles a single information about the entitlement from REMS.

    :returns: True if the user was found and the entitlement processed, False if not
    """
    application = data.get('application')
    resource = data.get('resource')
    user_oidc_id = data.get('user')
    email = data.get('mail')

    logger.debug(f'REMS :: * application_id: {application}, user_oidc_id: {user_oidc_id}, user_email: {email}, resource: {resource}')

    try:
        Dataset.objects.get(elu_accession=resource)
    except Dataset.DoesNotExist:
        message = f'REMS :: Dataset with such `elu_accession` ({resource}) does not exist! Quitting'
        logger.error(f' * {message}')
        # TODO: E2E: Save and display a notification to DataStewards
        raise ValueError(message)
    
    # First, tries to find a user with given OIDC ID
    # Then, it tries to find a contact with given OIDC ID
    # Then, it tries to find a user with given email address
    # Then, it tries to find a contact with given email address
    # If no account was found that far, then it will raise an error

    users_by_oidc = User.objects.filter(oidc_id=user_oidc_id)
    contacts_by_oidc = Contact.objects.filter(oidc_id=user_oidc_id)
    users_by_email = User.objects.filter(email=email)
    contacts_by_email = Contact.objects.filter(email=email)

    logger.debug(f'REMS :: Locating the User/Contact for the given Access information...')
    

    if users_by_oidc.count() + contacts_by_oidc.count() > 1:
        logger.error(f'REMS :: error, found multiple users or contacts with given OIDC_ID: {user_oidc_id}!')
        # Something is wrong - there are multiple users or contacts with given OIDC ID
        # TODO: E2E: Save and display a notification to DataStewards
        return False

    if users_by_oidc.count() == 1:
        logger.debug(f'REMS :: OK, found a user with given OIDC_ID')
        user = users_by_oidc.first()
        return create_rems_entitlement(user, application, resource, user_oidc_id, email)
    logger.debug(f'REMS :: no users with given OIDC_ID')

    if contacts_by_oidc.count() == 1:
        contact = contacts_by_oidc.first()
        logger.debug(f'REMS :: OK, found a contact with given OIDC_ID')
        return create_rems_entitlement(contact, application, resource, user_oidc_id, email)
    logger.debug(f'REMS :: no contacts with given OIDC_ID')

    if users_by_email.count() + contacts_by_email.count() > 1:
        logger.error(f'REMS :: error, found multiple users or contacts with given email: {email}!')
        # Something is wrong - there are multiple users or contacts with given OIDC ID
        # TODO: E2E: Save and display a notification to DataStewards
        return False

    if users_by_email.count() == 1:
        logger.debug(f'REMS :: OK, found a user with given email')
        user = users_by_email.first()
        return create_rems_entitlement(user, application, resource, user_oidc_id, email)
    logger.debug(f'REMS :: no users with given email')

    if contacts_by_email.count() == 1:
        contact = contacts_by_email.first()
        logger.debug(f'REMS :: OK, found a contact with given email')
        return create_rems_entitlement(contact, application, resource, user_oidc_id, email)
    logger.debug(f'REMS :: no contacts with given email')
    
    # At this moment, we didn't find any User nor Contact with given OIDC_ID nor email
    # Will attempt to create a new contact then
    Contact.get_or_create(email, user_oidc_id, resource)

    # TODO: E2E: Save and display a notification to DataStewards
    return True


def create_rems_entitlement(obj: Union[Access, User], 
        application: str, 
        dataset_id: str, 
        user_oidc_id: str, 
        email: str) -> bool:
    """
    Tries to find a dataset with `elu_accession` equal to `dataset_id`.
    If it exists, it will add a new logbook entry (Access object) set to the current user/contact
    Assumes that the Dataset exists, otherwise will throw an exception.
    """
    notes = f'Set automatically by REMS application #{application}'

    dataset = Dataset.objects.get(elu_accession=dataset_id)

    # The password is not a hash, therefore it is
    # not possible to log into this account
    system_rems_user, _ = User.objects.get_or_create(
        username='system::REMS',
        first_name=':REMS:',
        last_name=':System Account:',
        password='this_is_incorrect',
        email='lcsb-sysadmins+REMS@uni.lu'
    )
    
    if type(obj) == User:
        new_logbook_entry = Access(
            user=obj,
            dataset=dataset,
            access_notes=notes,
            granted_on=datetime.now(),
            was_generated_automatically=True,
            created_by=system_rems_user
        )
    elif type(obj) == Contact:
        new_logbook_entry = Access(
            contact=obj,
            dataset=dataset,
            access_notes=notes,
            granted_on=datetime.now(),
            was_generated_automatically=True,
            created_by=system_rems_user
        )
    else:
        klass = obj.__class__.__name__
        raise TypeError(f'Wrong type of the object - should be Contact or User, is: {klass} instead')
        
    new_logbook_entry.save()
    return True
