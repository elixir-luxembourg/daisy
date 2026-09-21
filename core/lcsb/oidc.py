import time
from collections import defaultdict
from typing import Dict, List, Optional, TypedDict

from django.conf import settings
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError, KeycloakAuthenticationError

from core.constants import IdentityProvider
from core.synchronizers import (
    AccountSynchronizationBackend,
    ExternalUserNotFoundException,
    OIDCUser,
)
from core.utils import DaisyLogger, normalized_email

logger = DaisyLogger(__name__)


def identity_provider_of(username: Optional[str]) -> Optional[IdentityProvider]:
    """
    The identity provider that the username suffix suggests, `john.doe|ul` -> UL. A label only:
    no suffix, or an unknown one, gives None and no decision may depend on it.
    """
    if not username:
        return None
    local_username, _, suffix = username.rpartition("|")
    return IdentityProvider.from_username_suffix(suffix) if local_username else None


def provider_label(account: OIDCUser) -> str:
    """The identity provider of an account, its username when the suffix says nothing."""
    if account.identity_provider:
        return account.identity_provider.display_name
    return account.username or "Keycloak"


def accounts_by_email(accounts: List[OIDCUser]) -> Dict[str, List[OIDCUser]]:
    """
    Group the accounts by email, one email can hold several. An account without an email is a
    system account, it is left out.
    """
    grouped = defaultdict(list)
    for account in accounts:
        email = normalized_email(account.email)
        if email:
            grouped[email].append(account)
    return grouped


class KeycloakUserResponse(TypedDict, total=False):
    id: str
    username: str
    firstName: str
    lastName: str
    email: str
    emailVerified: bool
    enabled: bool
    createdTimestamp: int
    totp: bool
    disableableCredentialTypes: List[str]
    requiredActions: List[str]
    notBefore: int
    access: Dict[str, bool]


class ExternalUserNotVerifiedException(ExternalUserNotFoundException):
    pass


def get_keycloak_config_from_settings() -> Dict:
    # settings.py defines the KEYCLOAK_* values only when KEYCLOAK_INTEGRATION is on
    return {
        "KEYCLOAK_URL": getattr(settings, "KEYCLOAK_URL", None),
        "KEYCLOAK_REALM_LOGIN": getattr(settings, "KEYCLOAK_REALM_LOGIN", None),
        "KEYCLOAK_REALM_ADMIN": getattr(settings, "KEYCLOAK_REALM_ADMIN", None),
        "KEYCLOAK_USER": getattr(settings, "KEYCLOAK_USER", None),
        "KEYCLOAK_PASS": getattr(settings, "KEYCLOAK_PASS", None),
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

    def get_keycloak_admin_connection(self) -> KeycloakAdmin:
        if self.keycloak_admin_connection is None:
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
        keycloak_response: List[KeycloakUserResponse] = (
            self.get_keycloak_admin_connection().get_users({"emailVerified": True})
        )
        return [
            self._build_oidc_user(user)
            for user in keycloak_response
            if user.get("emailVerified", False)
        ]

    def get_users_by_email(self, email: str) -> List[OIDCUser]:
        keycloak_response: List[
            KeycloakUserResponse
        ] = self.get_keycloak_admin_connection().get_users(
            {"email": email, "exact": True}
        )
        return [
            self._build_oidc_user(user)
            for user in keycloak_response
            if user.get("emailVerified", False)
        ]

    @staticmethod
    def _build_oidc_user(user: KeycloakUserResponse) -> OIDCUser:
        # the username keeps the identity provider suffix, `john.doe|ul`
        username = user.get("username")
        return OIDCUser(
            id=user.get("id"),
            email=user.get("email"),
            first_name=user.get("firstName"),
            last_name=user.get("lastName"),
            username=username,
            identity_provider=identity_provider_of(username),
            email_verified=user.get("emailVerified"),
            enabled=user.get("enabled"),
        )

    def get_external_user_info(self, oidc_id: str) -> OIDCUser:
        """
        Return the Keycloak account for this oidc_id
        """
        try:
            keycloak_response: KeycloakUserResponse = (
                self.get_keycloak_admin_connection().get_user(oidc_id)
            )
        except KeycloakGetError as e:
            raise ExternalUserNotFoundException(e)
        # We ignore users that are not verified
        if not keycloak_response.get("emailVerified", False):
            raise ExternalUserNotVerifiedException(
                f"User {oidc_id} is not verified in Keycloak!"
            )
        return self._build_oidc_user(keycloak_response)
