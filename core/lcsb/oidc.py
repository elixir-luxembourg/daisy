import json

from typing import Dict, List, Tuple

from django.conf import settings
from core.models.contact_type import ContactType
from core.utils import DaisyLogger
from keycloak import KeycloakAdmin

from core.models.contact import Contact
from core.models.partner import Partner
from core.models.user import User
from core.synchronizers import AccountSynchronizationException, AccountSynchronizationMethod, AccountSynchronizer


logger = DaisyLogger(__name__)


def get_keycloak_config_from_settings() -> Dict:
    return {
        'KEYCLOAK_URL': getattr(settings, 'KEYCLOAK_URL'),
        'KEYCLOAK_REALM': getattr(settings, 'KEYCLOAK_REALM'),
        'KEYCLOAK_USER': getattr(settings, 'KEYCLOAK_USER'),
        'KEYCLOAK_PASS': getattr(settings, 'KEYCLOAK_PASS')
    }


class KeycloakSynchronizationMethod(AccountSynchronizationMethod):
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
            server_url=self.config.get('KEYCLOAK_URL'),
            realm_name=self.config.get('KEYCLOAK_REALM'),
            username=self.config.get('KEYCLOAK_USER'),
            password=self.config.get('KEYCLOAK_PASS'),
            verify=False
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
                'first_name': user.get('firstName', 'FIRST_NAME_MISSING'),
                'last_name': user.get('lastName', 'FIRST_NAME_MISSING'),
                'username': user.get('email')
            } for user in keycloak_response if user.get('email', None) is not None
        ]


class KeycloakAccountSynchronizer(AccountSynchronizer):
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
                logger.debug('Received a record about a User without email from Keycloak')
            count_of_users = User.objects.filter(email=external_account.get('email')).count()
            if count_of_users == 1:
                User.objects.filter(email=external_account.get('email')).count()
                to_be_patched.append(external_account)
            elif count_of_users > 1:
                raise AccountSynchronizationException(f"There is more than 1 account with such an email: {external_account.get('email')}")
            elif count_of_users == 0:
                to_be_created.append(external_account)
        logger.debug('Detected ' + str(len(to_be_created)) + ' account(s) that are not existing in DAISY, and ' + str(len(to_be_patched)) + ' account(s) that need patching.')
        return to_be_created, to_be_patched

    def _add_users(self, list_of_users: List[Dict]):
        if len(list_of_users):
            contact_type, _ = ContactType.objects.get_or_create(name='Other')
            partner, _ = Partner.objects.get_or_create(acronym='Imported from Keycloak', name='Imported from Keycloak')
        for user_to_be in list_of_users:
            first_name = user_to_be.get('first_name', '-')
            last_name = user_to_be.get('last_name', '-')
            email = user_to_be.get('email')
            oidc_id = user_to_be.get('id'), 
            username = user_to_be.get('username')
            new_contact = Contact(email=email, oidc_id=oidc_id, first_name=first_name, last_name=last_name, contact_type=contact_type)
            new_contact.save()
            new_contact.partners.add(partner)
            new_contact.save()
        if len(list_of_users) > 0:
            logger.debug('Added ' + str(len(list_of_users)) + ' new user entries:')
        for user_to_be in list_of_users:
            logger.debug('OIDC_ID = ' + user_to_be.get('id'))

    def _patch_users(self, list_of_users: List[Dict]):
        logger.debug(str(list_of_users))
        for new_user_info in list_of_users:
            existing_user = User.objects.get(email=new_user_info.get('email'))
            logger.debug('Patching the OIDC_ID of the user: ' + new_user_info.get('email'))
            # Update just OIDC ID
            existing_user.oidc_id = new_user_info.get('id')
            # Don't actually patch these features
            # existing_user.email = new_user_info.get('email')
            # existing_user.first_name = new_user_info.get('first_name')
            # existing_user.last_name = new_user_info.get('last_name')
            existing_user.save()
        logger.debug('Updated ' + str(len(list_of_users)) + ' user entry(entries)')


class CachedKeycloakAccountSynchronizer(KeycloakAccountSynchronizer):
    def __init__(self, synchronizer: AccountSynchronizationMethod):
        super().__init__(synchronizer)
        self.current_external_accounts = []
        self._cached_external_accounts = None

    def synchronize(self) -> None:
        """This will fetch the accounts from external source and use them to synchronize DAISY accounts"""
        logger.debug('Keycloak Synchronization - Using the CachedKeycloakAccountSynchronizer')

        if self.current_external_accounts is not None:
            self._cached_external_accounts = self.current_external_accounts
        
        logger.debug('Keycloak Synchronization - Updating the cache...')
        self.current_external_accounts = self.synchronizer.get_list_of_users()

        if self._cached_external_accounts is None or self._did_something_change():
            accounts_to_be_created, accounts_to_be_patched = self.compare()
            logger.debug('Keycloak Synchronization - (1/3) ...compared the accounts...')

            self._add_users(accounts_to_be_created)
            logger.debug('Keycloak Synchronization - (2/3) ...added the users...')
            
            self._patch_users(accounts_to_be_patched)
            logger.debug('Keycloak Synchronization - (3/3) ...patched the accounts. Finished!')
        else:
            logger.debug('Keycloak Synchronization - ...Skipping the keycloak account synchronization pass, no changes detected')

    def _did_something_change(self):
        if self._cached_external_accounts is None or self.current_external_accounts is None:
            return True
        else:
            return self._cached_external_accounts != self.current_external_accounts
