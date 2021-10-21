import json

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request

from django.conf import settings
from keycloak import KeycloakAdmin

from core.models.cohort import Cohort
from core.models.dataset import Dataset
from core.models.partner import Partner
from core.models.project import Project
from core.models import User
from core.models.utils import CoreTrackedModel


def _http_post(url: str, data: Dict, timeout: int=6):
    encoded_data = json.dumps(data).encode('utf8')
    request = Request(url, encoded_data)
    request.add_header('Content-Type', 'application/json')
    response = urlopen(request, timeout=timeout).read().decode('utf-8')
    return response

def _call_idservice(entity_type: str, name: Optional[str]=None):
    url = getattr(settings, 'IDSERVICE_ENDPOINT')
    data = {
        "entity": entity_type,
    }
    if name is not None:
        data['name'] = name
    return _http_post(url, data)

def generate_identifier(obj: CoreTrackedModel, save=True):
    klass = type(obj).__name__
    if not isinstance(obj, (Dataset, Project, Cohort, Partner)):
        msg = f'Unrecognized entity! (Only Project, Dataset, Cohort and Partner are recognized; got - {klass})'
        raise ValueError(msg)
    
    if hasattr(obj, 'title'):
        title = obj.title
    elif hasattr(obj, 'name'):
        title = obj.name
    else:
        msg = f'Cannot find the object''s name! (The object of class {klass} does not have title nor name attribute!'
        raise KeyError(msg)

    the_id = _call_idservice(klass.lower(), title)
    return the_id


def get_config_from_settings() -> Dict:
    return {
        'KEYCLOAK_URL': getattr(settings, 'KEYCLOAK_URL'),
        'KEYCLOAK_REALM': getattr(settings, 'KEYCLOAK_REALM'),
        'KEYCLOAK_USER': getattr(settings, 'KEYCLOAK_USER'),
        'KEYCLOAK_PASS': getattr(settings, 'KEYCLOAK_PASS')
    }


class AccountSynchronizationMethod:
    @abstractmethod
    def get_list_of_users(self) -> List[Dict]:
        pass

    @abstractmethod
    def test_connection(self) -> None:
        pass

class AccountSynchronizationException(Exception):
    pass

class KeycloakSynchronization(AccountSynchronizationMethod):
    def __init__(self, config: Dict, connect=True) -> None:
        self.config = config
        self.keycloak_admin_connection = self._create_connection(config) if connect else None

    @staticmethod
    def _validate_config(config: Dict) -> None:
        keys = ['KEYCLOAK_URL', 'KEYCLOAK_USER', 'KEYCLOAK_PASS', 'KEYCLOAK_REALM']
        for key in keys:
            if key not in config:
                raise KeyError(f"'{key}' missing in KeycloakAdmin configuration!")

    def get_keycloak_admin_connection(self) -> None:
        if self.keycloak_admin_connection is not None:
            self.keycloak_admin_connection = self._create_connection(self.config)
        
        return self.keycloak_admin_connection

    def _create_connection(self, config:Dict=None) -> KeycloakAdmin:
        if config is not None:
            self.config = config
        
        self._validate_config(self.config) 
        admin = KeycloakAdmin(
            self.config.get('KEYCLOAK_URL'),
            self.config.get('KEYCLOAK_REALM'),
            self.config.get('KEYCLOAK_USER'),
            self.config.get('KEYCLOAK_PASS')
        )
        return admin

    def test_connection(self) -> bool:
        try:
            config_well_know = self.get_keycloak_admin_connection().well_know()
            return True
        except:
            return False

    def get_list_of_users(self) -> List[Dict]:
        keycloak_response = self.get_keycloak_admin_connection().get_users({})
        return [
            {
                'id': user.get('id'), 
                'email': user.get('email', 'EMAIL_MISSING'),
                # TODO: First name
                # TODO: Last name
            } for user in keycloak_response
        ]


class EmptyAccountSynchronizer:
    def __init__(self, synchronizer: AccountSynchronizationMethod=None):
        pass

    def test_connection(self):
        return True

    def compare(self) -> Tuple[List, List]:
        return [], []

    def synchronize(self) -> None:
        pass

class DummySynchronization(AccountSynchronizationMethod):
    def __init__(self, config: Dict=None, connect=False) -> None:
        pass

    def test_connection(self) -> bool:
        return True
        
    def get_list_of_users(self) -> List[Dict]:
        return []

class AccountSynchronizer:
    def __init__(self, synchronizer: AccountSynchronizationMethod):
        """We'll need a way to fetch accounts to synchronize"""
        self.synchronizer = synchronizer
        self.test_connection()

    def test_connection(self) -> bool:
        if self.synchronizer is not None:
            return self.synchronizer.test_connection()
        return False

    def synchronize(self) -> None:
        """This will fetch the accounts from external source and use them to synchronize DAISY accounts"""
        self.current_external_accounts = self.synchronizer.get_list_of_users()
        accounts_to_be_created, accounts_to_be_patched = self.compare()
        self._add_users(accounts_to_be_created)
        self._patch_users(accounts_to_be_patched)

    def compare(self) -> Tuple[list, list]:
        to_be_created = []
        to_be_patched = []
        for external_account in self.current_external_accounts:
            if external_account.get('email', None) is None:
                raise AccountSynchronizationException(f"Received a record without an email!")
            count_of_users = User.objects.filter(email=external_account.get('email')).count()
            if count_of_users == 1:
                to_be_patched.append(external_account)
            elif count_of_users > 1:
                raise AccountSynchronizationException(f"There is more than 1 account with such an email: {external_account.get('email')}")
            elif count_of_users == 0:
                to_be_created.append(external_account)
        return to_be_created, to_be_patched

    def _add_users(self, list_of_users: List[Dict]):
        for user_to_be in list_of_users:
            first_name = user_to_be.get('first_name', '-')
            last_name = user_to_be.get('last_name', '-')
            email = user_to_be.get('email')
            oidc_id = user_to_be.get('id')
            new_user = User(email=email, oidc_id=oidc_id, first_name=first_name, last_name=last_name)
            new_user.save()

    def _patch_users(self, list_of_users: List[Tuple[User, Dict]]):
        for (existing_user, new_user_info) in list_of_users:
            existing_user.oidc_id = new_user_info.get('id')
            existing_user.email = new_user_info.get('email')
            existing_user.first_name = new_user_info.get('first_name')
            existing_user.last_name = new_user_info.get('last_name')
            existing_user.save()


# How to continue:
# 5. Code that triggers whole the process
# 6. Tests of process of comparation
# 7. Tests of the whole process with mocks

