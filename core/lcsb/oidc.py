from typing import Dict, List, Optional, Tuple

from django.conf import settings
from keycloak import KeycloakAdmin
from keycloak.exceptions import (
    KeycloakGetError,
    KeycloakAuthenticationError,
    KeycloakOperationError,
)

from core.synchronizers import (
    AccountSynchronizationBackend,
    AccountSynchronizer,
    ExternalUserNotFoundException,
    InconsistentSynchronizerStateException,
)
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)


class ExternalUserNotVerifiedException(ExternalUserNotFoundException):
    pass


def get_keycloak_config_from_settings() -> Dict:
    return {
        "KEYCLOAK_URL": getattr(settings, "KEYCLOAK_URL"),
        "KEYCLOAK_REALM_LOGIN": getattr(settings, "KEYCLOAK_REALM_LOGIN"),
        "KEYCLOAK_REALM_ADMIN": getattr(settings, "KEYCLOAK_REALM_ADMIN"),
        "KEYCLOAK_USER": getattr(settings, "KEYCLOAK_USER"),
        "KEYCLOAK_PASS": getattr(settings, "KEYCLOAK_PASS"),
    }


class KeycloakSynchronizationBackend(AccountSynchronizationBackend):
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
        admin = KeycloakAdmin(
            server_url=self.config.get("KEYCLOAK_URL"),
            realm_name=self.config.get("KEYCLOAK_REALM_ADMIN"),
            user_realm_name=self.config.get("KEYCLOAK_REALM_LOGIN"),
            username=self.config.get("KEYCLOAK_USER"),
            password=self.config.get("KEYCLOAK_PASS"),
            verify=self.config.get("KEYCLOAK_SSL_VERIFY", True),
        )
        return admin

    def test_connection(self) -> bool:
        try:
            _ = self.get_keycloak_admin_connection().users_count()
            return True
        except (KeyError, KeycloakAuthenticationError, KeycloakOperationError):
            return False

    def get_list_of_users(self) -> List[Dict]:
        keycloak_response = self.get_keycloak_admin_connection().get_users(
            {"emailVerified": True}
        )
        return [
            {
                "id": user.get("id"),
                "email": user.get("email", None),
                "firstName": user.get("firstName"),
                "lastName": user.get("lastName"),
            }
            for user in keycloak_response
            if user.get("emailVerified", False)
        ]

    def get_external_user_info(self, oidc_id: str) -> Dict[str, str]:
        """
        Should return a dictionary with the external user information
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
        return keycloak_response


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

    def build_user_or_contact_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy User model
        """
        return {
            "first_name": external_user_information.get(
                "firstName", "FIRST_NAME_MISSING"
            ),
            "last_name": external_user_information.get("lastName", "LAST_NAME_MISSING"),
            "email": external_user_information.get("email"),
            "id": external_user_information.get("id"),
        }

    def build_user_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy User model
        """
        return self.build_user_or_contact_dict(external_user_information)

    def build_contact_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy Contact model
        """
        return self.build_user_or_contact_dict(external_user_information)

    def synchronize_single_account(
        self, acc: Dict[str, Optional[str]]
    ) -> Optional[Tuple[str, str]]:
        # accounts without emails are system accounts and can be skipped
        if not acc.get("email"):
            logger.debug(f"Skipping account without email for id {acc.get('id')}")
            return
        try:
            self.update_user_or_contact(
                acc, acc.get("id"), acc.get("email"), create_contact_if_not_found=True
            )
        except InconsistentSynchronizerStateException as e:
            logger.error(e)
