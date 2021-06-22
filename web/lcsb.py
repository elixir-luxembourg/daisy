import json
import logging

from typing import Dict

from django.conf import settings
from django.http import HttpRequest

from core.models.user import User
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)

def handle_rems_callback(request: HttpRequest) -> bool:
    """
    Handles an entitlements request coming from REMS
    More information on:
    https://rems2docs.rahtiapp.fi/configuration/#entitlements

    :returns: True if everything was processed, False if not
    """
    logger.debug('Unpacking the data received from REMS...')
    body_unicode = request.body.decode('utf-8')
    request_post_data = json.loads(body_unicode)

    if not isinstance(request_post_data, list):
        the_type = type(request_post_data)
        message = f'Received wrong data (it is not a list, but {the_type}!'
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

    logger.debug(f'* application_id: {application}, user: {user_id}@{email}, resource: {resource}')

    method = getattr(settings, 'REMS_MATCH_USERS_BY', 'email').lower()
    if method == 'email':
        user = User.objects.get(email=email)
    elif method == 'id':
        user = User.objects.get(oidc_id=user_id)
    else:
        raise ValueError(f"'REMS_MATCH_USERS_BY' must contain either 'id' or 'email', but has: {method} instead!")

    return user.add_rems_entitlement(application, resource, user_id, email)
