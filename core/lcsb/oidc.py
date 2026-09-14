import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError, KeycloakAuthenticationError

from core.constants import IdentityProvider
from core.synchronizers import (
    AccountSynchronizationBackend,
    AccountSynchronizer,
    ExternalUserNotFoundException,
    InconsistentSynchronizerStateException,
    OIDCUser,
)
from core.utils import DaisyLogger

logger = DaisyLogger(__name__)


def parse_oidc_username(
    username: Optional[str],
) -> Tuple[Optional[str], Optional[IdentityProvider]]:
    if not username:
        return username, None

    local_username, _, suffix = username.rpartition("|")
    provider = IdentityProvider.from_username_suffix(suffix) if local_username else None
    return (local_username, provider) if provider else (username, None)


class ExternalUserNotVerifiedException(ExternalUserNotFoundException):
    pass


def get_keycloak_config_from_settings() -> Dict:
    return {
        "KEYCLOAK_URL": getattr(settings, "KEYCLOAK_URL"),
        "KEYCLOAK_REALM_LOGIN": getattr(settings, "KEYCLOAK_REALM_LOGIN"),
        "KEYCLOAK_REALM_ADMIN": getattr(settings, "KEYCLOAK_REALM_ADMIN"),
        "KEYCLOAK_USER": getattr(settings, "KEYCLOAK_USER"),
        "KEYCLOAK_PASS": getattr(settings, "KEYCLOAK_PASS"),
        "KEYCLOAK_MAX_RETRIES": getattr(settings, "KEYCLOAK_MAX_RETRIES", 3),
        "KEYCLOAK_RETRY_DELAY": getattr(settings, "KEYCLOAK_RETRY_DELAY", 2),
    }


class KeycloakBackend(AccountSynchronizationBackend):
    def __init__(self, config: Dict, connect=True) -> None:
        self.config = config
        self.keycloak_admin_connection = (
            self._create_connection(config) if connect else None
        )

    @staticmethod
    def _validate_config(config: Dict) -> None:
        keys = [
            "KEYCLOAK_URL",
            "KEYCLOAK_USER",
            "KEYCLOAK_PASS",
            "KEYCLOAK_REALM_LOGIN",
            "KEYCLOAK_REALM_ADMIN",
            "KEYCLOAK_MAX_RETRIES",
            "KEYCLOAK_RETRY_DELAY",
        ]
        for key in keys:
            if key not in config:
                raise KeyError(f"'{key}' missing in KeycloakAdmin configuration!")

    def get_keycloak_admin_connection(self) -> None:
        if self.keycloak_admin_connection is not None:
            self.keycloak_admin_connection = self._create_connection(self.config)

        return self.keycloak_admin_connection

    def _create_connection(self, config: Dict = None) -> KeycloakAdmin:
        if config is not None:
            self.config = config

        self._validate_config(self.config)
        max_retries = self.config.get("KEYCLOAK_MAX_RETRIES")
        retry_delay = self.config.get("KEYCLOAK_RETRY_DELAY")
        for attempt in range(max_retries):
            try:
                admin = KeycloakAdmin(
                    server_url=self.config.get("KEYCLOAK_URL"),
                    realm_name=self.config.get("KEYCLOAK_REALM_ADMIN"),
                    user_realm_name=self.config.get("KEYCLOAK_REALM_LOGIN"),
                    username=self.config.get("KEYCLOAK_USER"),
                    password=self.config.get("KEYCLOAK_PASS"),
                    verify=self.config.get("KEYCLOAK_SSL_VERIFY", True),
                )
                return admin
            except KeycloakAuthenticationError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Keycloak authentication failed (attempt {attempt + 1}/{max_retries}), retrying..."
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached for Keycloak authentication.")
                    raise

    def test_connection(self) -> bool:
        try:
            _ = self.get_keycloak_admin_connection().users_count()
            return True
        except:
            return False

    def get_list_of_users(self) -> List[OIDCUser]:
        keycloak_response = self.get_keycloak_admin_connection().get_users(
            {"emailVerified": True}
        )
        return [
            self._build_oidc_user(user)
            for user in keycloak_response
            if user.get("emailVerified", False)
        ]

    def get_users_by_email(self, email: str) -> List[OIDCUser]:
        keycloak_response = self.get_keycloak_admin_connection().get_users(
            {"email": email, "exact": True}
        )
        return [
            self._build_oidc_user(user)
            for user in keycloak_response
            if user.get("emailVerified", False)
        ]

    @staticmethod
    def _build_oidc_user(user: Dict) -> OIDCUser:
        username, provider = parse_oidc_username(user.get("username"))
        return OIDCUser(
            id=user.get("id"),
            email=user.get("email", None),
            first_name=user.get("firstName"),
            last_name=user.get("lastName"),
            username=username,
            identity_provider=provider.display_name if provider else None,
        )

    def get_external_user_info(self, oidc_id: str) -> OIDCUser:
        """
        Return the Keycloak account for this oidc_id
        """
        try:
            keycloak_response = self.get_keycloak_admin_connection().get_user(oidc_id)
        except KeycloakGetError as e:
            raise ExternalUserNotFoundException(e)
        # We ignore users that are not verified
        if not keycloak_response.get("emailVerified", False):
            raise ExternalUserNotVerifiedException(
                f"User {oidc_id} is not verified in Keycloak!"
            )
        return self._build_oidc_user(keycloak_response)


class KeycloakAccountSynchronizer(AccountSynchronizer):
    def __init__(self, synchronizer_backend: AccountSynchronizationBackend):
        """We'll need a way to fetch accounts to synchronize"""
        self.synchronizer_backend = synchronizer_backend
        self.test_connection()

    def test_connection(self) -> bool:
        if self.synchronizer_backend is not None:
            return self.synchronizer_backend.test_connection()
        return False

    def synchronize_all(self) -> None:
        """This will fetch the accounts from external source and use them to synchronize DAISY accounts"""
        current_external_accounts = self.synchronizer_backend.get_list_of_users()
        for external_account in current_external_accounts:
            self.synchronize_single_account(external_account)

    def build_user_or_contact_dict(self, account: OIDCUser) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy User model
        """
        return {
            "first_name": account.first_name or "FIRST_NAME_MISSING",
            "last_name": account.last_name or "LAST_NAME_MISSING",
            "email": account.email,
            "id": account.id,
        }

    def build_user_dict(self, account: OIDCUser) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy User model
        """
        return self.build_user_or_contact_dict(account)

    def build_contact_dict(self, account: OIDCUser) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy Contact model
        """
        return self.build_user_or_contact_dict(account)

    def synchronize_single_account(self, account: OIDCUser) -> None:
        # accounts without emails are system accounts and can be skipped
        if not account.email:
            logger.debug(f"Skipping account without email for id {account.id}")
            return
        try:
            self.update_user_or_contact(
                account, account.id, account.email, create_contact_if_not_found=True
            )
        except InconsistentSynchronizerStateException as e:
            logger.error(e)
