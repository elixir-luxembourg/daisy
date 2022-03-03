import json

from multiprocessing import Lock
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from keycloak import KeycloakAdmin

from core.models.contact_type import ContactType
from core.models.contact import Contact
from core.models.partner import Partner
from core.models.user import User
from core.synchronizers import AccountSynchronizationException, AccountSynchronizationMethod, AccountSynchronizer
from core.utils import DaisyLogger


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
                'id': user.get('id').replace(',', '').replace('(', '').replace(')', '').replace("'", ''), 
                'email': user.get('email', None),
                'first_name': user.get('firstName', 'FIRST_NAME_MISSING'),
                'last_name': user.get('lastName', 'LAST_NAME_MISSING'),
                'username': user.get('email', 'USERNAME_MISSING')
            } for user in keycloak_response
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
        for external_account in self.current_external_accounts:
            self.synchronize_single_account(external_account)

    def synchronize_system_account(self, acc):
        user, _ = User.objects.get_or_create(
            username=acc.get('username').replace('"', '').replace("'", '').replace('(', '').replace(')', '').replace(",", ''),
        )
        user.oidc_id = acc.get('id')
        user.email = f'lcsb.sysadmins+{acc.get("id")}@uni.lu'
        user.save()

    def synchronize_single_account(self, acc: Dict[str, Optional[str]]) -> Optional[Tuple[str, str]]:
        # First, check if this is a special case of system accounts - in such case create the account if needed
        if 'system::' in acc.get('username', ''):
            logger.debug(f'KC :: Found system account with this OIDC ID: {acc.get("id")}!')
            self.synchronize_system_account(acc)

        # Then, check if a User with given OIDC exists - skip in such case
        user_count = User.objects.filter(oidc_id=acc.get('id')).count()
        if user_count == 1:
            logger.debug(f'KC :: Found the User with this OIDC ID: {acc.get("id")}.')
            return None
        if user_count > 1:
            logger.warning(f'KC :: Found multiple User accounts with this OIDC ID: {acc.get("id")}!')
            return None

        # Then. check if Contact with given OIDC exists - skip in such case
        contact_count = Contact.objects.filter(oidc_id=acc.get('id')).count()
        if contact_count == 1:
            logger.debug(f'KC :: Found the Contact with this OIDC ID: {acc.get("id")}.')
            return None
        if contact_count > 1:
            logger.warning(f'KC :: Found multiple Contact accounts with this OIDC ID: {acc.get("id")}!')
            return None

        # If we didn't exit so far, we can assume that we need to patch a User or a Contact, if they have already an account with set email address
        # Let's try to find user with given e-mail
        user_by_email = User.objects.filter(email=acc.get('email'))
        if user_by_email.count() == 1:
            user:User = user_by_email.first()
            user.oidc_id = acc.get('id')
            user.save()
            logger.debug(f'KC :: Set OIDC_ID ({acc.get("id")}) of a existing User (matched by email)')
            return ('User', 'patched',)
        elif user_by_email.count() > 1:
            logger.error(f'KC :: Found multiple User accounts with this email: {acc.get("email")}!')
            raise KeyError(f'KC :: Found multiple User accounts with this email: {acc.get("email")}!')

        # Then, let's try to find a contact with a given email - if it's there, let's patch it
        contacts_by_email = Contact.objects.filter(email=acc.get('email'))
        if contacts_by_email.count() >= 1:
            logger.debug(f'KC :: Found the Contact with this OIDC ID (matched by email): {acc.get("id")}.')
            contact:Contact = contacts_by_email.first()
            contact.oidc_id = acc.get('id')
            contact.save()
            return ('Contact', 'patched',)

        # If we didn't exit so far, then we need to add a Contact with the new information
        logger.debug(f'KC :: Creating a new Contact for {acc.get("id")}')
        self.add_contact(acc)
        return ('Contact', 'created')

    def add_contact(self, contact_to_be: Dict[str, Optional[str]]):
        contact_type, _ = ContactType.objects.get_or_create(name='Other')
        partner, _ = Partner.objects.get_or_create(acronym='Imported from Keycloak', name='Imported from Keycloak')
        first_name = contact_to_be.get('first_name', '-')
        last_name = contact_to_be.get('last_name', '-')
        email = contact_to_be.get('email')
        oidc_id = contact_to_be.get('id')
        username = contact_to_be.get('username')
        new_contact = Contact(email=email, oidc_id=oidc_id, first_name=first_name, last_name=last_name, type=contact_type)
        new_contact.save()
        new_contact.partners.add(partner)
        new_contact.save()
    
    def check_for_problems(self) -> bool:
        status = False
        logger.debug(f'KC :: checking for problems in {len(self.current_external_accounts)} incoming entries')

        if len(self.current_external_accounts) == 0:
            return False

        for entry in self.current_external_accounts:
            email = entry.get('email')
            oidc_id = entry.get('id')

            u = User.objects.filter(email=email)
            c = Contact.objects.filter(email=email)
            if u.count() + c.count() > 1:
                logger.warning(f'KC :: problem found - multiple accounts with the same email address ({email}) found!')
                status = True

            u2 = User.objects.filter(oidc_id=oidc_id)
            c2 = Contact.objects.filter(oidc_id=oidc_id)
            if u2.count() + c2.count() > 1:
                logger.warning(f'KC :: problem found - multiple accounts with the same oidc_id ({oidc_id}) found!')
                status = True

        return status

class CachedKeycloakAccountSynchronizer(KeycloakAccountSynchronizer):
    def __init__(self, synchronizer: AccountSynchronizationMethod):
        super().__init__(synchronizer)
        cid = id(self)
        logger.debug(f'KC :: Keycloak Cached Synchronization #{cid} - initialized with an empty cache')
        self.current_external_accounts = []
        self._cached_external_accounts = None
        self.lock = Lock()

    @transaction.atomic
    def synchronize(self) -> None:
        """This will fetch the accounts from external source and use them to synchronize DAISY accounts"""
        logger.debug('KC :: Keycloak Synchronization - 1. Using the CachedKeycloakAccountSynchronizer')

        _ = User.objects.select_for_update().all()

        try:
            self.lock.acquire()  # Warning: it might not be the best method for synchronization across different threads, because it relies on the way how the server is spawned
            logger.debug(f'KC :: Keycloak Synchronization - 2. Acquired the lock #{id(self.lock)}')

            if self.current_external_accounts is not None:
                self._cached_external_accounts = self.current_external_accounts
            
            logger.debug('KC :: Keycloak Synchronization - 3. Updating the cache...')
            self.current_external_accounts = self.synchronizer.get_list_of_users()

            if self._cached_external_accounts is None or self._did_something_change():
                logger.debug('KC :: Keycloak Synchronization - 4. Checking for problems')
                self.check_for_problems()

                # Perform the actual synchronization
                logger.debug(f'KC :: Keycloak Synchronization - 5. Iterating over the incoming information ({len(self.current_external_accounts)})')
                for external_account in self.current_external_accounts:
                    self.synchronize_single_account(external_account)

            else:
                logger.debug('KC :: Keycloak Synchronization - 5b No changes detected, skipping the account synchronization')
        except Exception as ex:
            logger.error(f'KC :: Exception while synchronizing... {ex}')
        finally:
            logger.debug(f'KC :: Keycloak Synchronization - 6. Freeing the lock #{id(self.lock)}')
            self.lock.release()

    def _did_something_change(self):
        if self._cached_external_accounts is None or self.current_external_accounts is None:
            return True
        else:
            return self._cached_external_accounts != self.current_external_accounts
    