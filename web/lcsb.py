import json
import logging

from typing import Dict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from core.lcsb import AccountSynchronizer, DummySynchronization, EmptyAccountSynchronizer, get_config_from_settings, KeycloakSynchronization
from core.models.contact import Contact
from core.models.dataset import Dataset
from core.models.user import User
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)

"""
if getattr(settings, 'KEYCLOAK_INTEGRATION', False) == True:
    keycloak_backend = KeycloakSynchronization(get_config_from_settings())
    synchronizer = AccountSynchronizer(keycloak_backend)
else:
    keycloak_backend = DummySynchronization()
    synchronizer = EmptyAccountSynchronizer()
"""

def handle_rems_callback(request: HttpRequest) -> bool:
    """
    Handles an entitlements request coming from REMS
    More information on:
    https://rems2docs.rahtiapp.fi/configuration/#entitlements

    :returns: True if everything was processed, False if not
    """

    """
    # Ensure the most recent account inforrmation by pulling it from Keycloak
    logger.debug('Refreshing the account information from Keycloak...')
    synchronizer.synchronize()
    """

    # TODO: Send an email to the Data Stewards or create a notification

    logger.debug('Unpacking the data received from REMS...')
    body_unicode = request.body.decode('utf-8')
    request_post_data = json.loads(body_unicode)

    if not isinstance(request_post_data, list):
        the_type = type(request_post_data)
        message = f'Received data with wrong format (it is not a list, but {the_type})!'
        raise TypeError(message)

    statuses = [handle_rems_entitlement(item) for item in request_post_data]
    return all(statuses)

def handle_rems_entitlement(data: Dict) -> bool:
    """
    Handles a single information about the entitlement from REMS.
    Relies on settings['REMS_MATCH_USERS_BY'] for a method of matching users (id/email)

    :returns: True if the user was found and the entitlement processed, False if not
    """
    application = data.get('application')
    resource = data.get('resource')
    user_id = data.get('user')
    email = data.get('mail')

    logger.debug(f'* application_id: {application}, user_id: {user_id}, user_email: {email}, resource: {resource}')

    method = getattr(settings, 'REMS_MATCH_USERS_BY', '-').lower()
    if method not in ['email', 'id', 'auto']:
        message = f"'REMS_MATCH_USERS_BY' must contain either 'id', 'email' or 'auto', but is: {method} instead!"
        logger.warn(message)
        raise ImproperlyConfigured(message)

    try:
        Dataset.objects.get(elu_accession=resource)
    except Dataset.DoesNotExist:
        message = f'Dataset with such `elu_accession` ({resource}) does not exist! Quitting'
        logger.debug(f' * {message}')
        raise ValueError(message)
    
    try:
        user = User.find_user_by_email_or_oidc_id(email, user_id, method)
        return user.add_rems_entitlement(application, resource, user_id, email)
    except Exception as ex:
        logger.debug(' * Didn''t find the user with such oidc id or email, will add a contact instead: ' + str(ex))
    
    try:
        contact = Contact.get_or_create(email, user_id, resource, method)
        return contact.add_rems_entitlement(application, resource, user_id, email)
    except Exception as ex:
        raise ValueError('Something went wrong during creating an entry for Access/Contact: ' + str(ex))

