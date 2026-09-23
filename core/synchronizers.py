from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.constants import IdentityProvider
from core.models import Contact, User, UserSource
from core.utils import DaisyLogger, normalized_email, records_with_email

logger = DaisyLogger(__name__)


class AccountSynchronizationException(Exception):
    pass


class ExternalUserNotFoundException(AccountSynchronizationException):
    pass


@dataclass
class OIDCUser:
    id: str
    email: str
    first_name: str
    last_name: str
    username: str
    identity_provider: Optional[IdentityProvider] = None
    # a disabled account must not become an active DAISY user
    enabled: Optional[bool] = None


class AccountSynchronizationBackend(ABC):
    """
    Class that represents a method of obtaining the list of users
    which then will be used to synchronize the account informations
    """

    @abstractmethod
    def get_list_of_users(self) -> List[OIDCUser]:
        """
        Should return a list of OIDCUser objects with user information.
        """
        pass

    @abstractmethod
    def test_connection(self) -> None:
        """
        Should test the connection to the data source and raise an exception
        if there is something wrong
        """
        pass

    @abstractmethod
    def get_external_user_info(self, oidc_id: str) -> OIDCUser:
        """
        Should return the external account as an OIDCUser
        """
        pass


def create_user(account: OIDCUser) -> User:
    """
    Create a DAISY user for a Keycloak account, with the username that Keycloak gives, and an
    unusable password: the password lives in Keycloak.
    The username and the subject are unique in the realm, so a duplicate is an older DAISY row
    and it raises IntegrityError. The caller decides that the account needs a user.
    """
    user = User(
        username=account.username,
        email=normalized_email(account.email),
        first_name=account.first_name or "",
        last_name=account.last_name or "",
        oidc_id=account.id,
        source=UserSource.ACTIVE_DIRECTORY,
    )
    user.set_unusable_password()
    user.save()
    return user


def activated(user: User) -> User:
    """
    The row of a Keycloak subject is the person: a login and an entitlement activate it again
    instead of creating a second one. A person is blocked in Keycloak now, not with is_active.
    """
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
    return user


def get_contact(oidc_id: str, email: Optional[str] = None) -> Optional[Contact]:
    """
    The contact of this Keycloak subject, or of this email. A subject always becomes a user, so
    such a contact is a record to migrate: its access rows stay on the contact until then.
    """
    contact = Contact.objects.filter(oidc_id=oidc_id).first()
    if contact or not email:
        return contact
    contacts = records_with_email(Contact.objects.all(), email)
    return contacts[0] if contacts else None


def user_for_oidc_id(
    backend: AccountSynchronizationBackend, oidc_id: str, email: Optional[str] = None
) -> User:
    """
    The DAISY user of a Keycloak subject, for REMS, which names the subject and nothing else:
    the stored user of that subject, else the Keycloak account, which becomes a user.
    A contact is never the answer, it is only reported. An unknown subject raises
    ExternalUserNotFoundException. `email` is what REMS sent, for an account without one.
    """
    user = User.objects.filter(oidc_id=oidc_id).first()
    if user:
        return activated(user)

    contact = get_contact(oidc_id, email)
    if contact:
        logger.warning(
            f"Contact {contact.pk} holds the Keycloak subject {oidc_id} or its email: the "
            f"entitlement goes to a user, the access records of the contact need a migration"
        )
    account = backend.get_external_user_info(oidc_id)
    return bind_or_create_user(account, normalized_email(account.email or email))


def bind_or_create_user(account: OIDCUser, email: Optional[str] = None) -> User:
    """
    Bind the account to the DAISY user of its email when exactly one active user waits unbound,
    and create a user otherwise. An inactive user is never adopted: a login cannot activate a
    stored row, so the identity needs a user of its own.
    """
    candidates = records_with_email(
        User.objects.filter(oidc_id__isnull=True, is_active=True), email
    )
    if len(candidates) == 1:
        user = candidates[0]
        user.oidc_id = account.id
        user.save(update_fields=["oidc_id"])
        return user
    return create_user(account)


class DummySynchronizationBackend(AccountSynchronizationBackend):
    """The backend of an instance without the Keycloak integration: it knows no account."""

    def __init__(self, config: Dict = None, connect=False) -> None:
        pass

    def test_connection(self) -> bool:
        return True

    def get_list_of_users(self) -> List[OIDCUser]:
        return []

    def get_external_user_info(self, oidc_id: str) -> OIDCUser:
        raise ExternalUserNotFoundException(
            f"The Keycloak integration is off, DAISY cannot resolve the subject {oidc_id}"
        )
