from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Union, Type
from core.models import User, Contact, ContactType, Partner
from core.utils import DaisyLogger

logger = DaisyLogger(__name__)


class AccountSynchronizationException(Exception):
    pass


class InconsistentSynchronizerStateException(AccountSynchronizationException):
    pass


class ExternalUserNotFoundException(AccountSynchronizationException):
    pass


class NoUserOrContactFoundInDaisyException(AccountSynchronizationException):
    pass


class AccountSynchronizationBackend(ABC):
    """
    Class that represents a method of obtaining the list of users
    which then will be used to synchronize the account informations
    """

    @abstractmethod
    def get_list_of_users(self) -> List[Dict]:
        """
        Should return a list of dictionaries with user information,
        like: {'id': '', 'email': '', 'first_name': '', etc. }
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
    def get_external_user_info(self, oidc_id: str) -> Dict[str, str]:
        """
        Should return a dictionary with the user information
        """
        pass


def update_user_or_contact(
    user_or_contact_model: Union[Type[User], Type[Contact]],
    info: Dict[str, str],
    oidc_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[Union[User, Contact]]:
    """
    Update the user or contact record based on the information provided.
    User or contact are found based on the oidc_id or email.
    If the oidc_id is provided, the email is ignored.
    If the oidc_id is not provided, the email is used to find the user or contact but only select
     users without oidc_id
    If not match is found, function return None
    If a match is found and updated, the function return the updated entity
    """
    if not oidc_id and not email:
        return None
    if not oidc_id:
        try:
            entity = user_or_contact_model.objects.get(email=email)
        except user_or_contact_model.DoesNotExist:
            return None
        except user_or_contact_model.MultipleObjectsReturned as e:
            raise InconsistentSynchronizerStateException(
                f"Multiple {user_or_contact_model.__name__} found for this email {email}",
            ) from e
        # we only update users based on email if their oidc_id is not set
        if entity.oidc_id:
            raise InconsistentSynchronizerStateException(
                f"OIDC don't match for {user_or_contact_model.__name__} with email {email} {oidc_id} expected while {entity.oidc_id} found in daisy"
            )
    else:
        try:
            entity = user_or_contact_model.objects.get(oidc_id=oidc_id)
        except user_or_contact_model.DoesNotExist:
            return None
    update_and_save_entity(entity, info)
    entity.save()
    return entity


def update_user(
    user_info: Dict[str, str],
    oidc_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[User]:
    """
    Update the user record based on the information provided
    Returns True if a user for this oidc_id or email was found and updated, False otherwise
    """
    return update_user_or_contact(User, user_info, oidc_id, email)


def update_contact(
    contact_info: Dict[str, str],
    oidc_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[Contact]:
    """
    Update the contact record based on the information provided
    Returns True if a contact for this oidc_id was found and updated, False otherwise
    """
    return update_user_or_contact(Contact, contact_info, oidc_id, email)


def create_contact(contact_dict):
    contact = Contact()
    update_and_save_entity(contact, contact_dict)
    contact_type, _ = ContactType.objects.get_or_create(name="Other")
    partner, _ = Partner.objects.get_or_create(
        acronym="Imported from Keycloak", name="Imported from Keycloak"
    )
    contact.type = contact_type
    contact.save()
    contact.partners.add(partner)
    contact.save()
    return contact


def update_and_save_entity(entity, info):
    entity.last_name = info.get("last_name", entity.last_name)
    entity.first_name = info.get("first_name", entity.first_name)
    entity.email = info.get("email", entity.email)
    entity.oidc_id = info.get("id")


def check_inconsistent_state(oidc_id, email):
    users_by_oidc_count = User.objects.filter(oidc_id=oidc_id).count()
    contacts_by_oidc_count = Contact.objects.filter(oidc_id=oidc_id).count()
    if (users_by_oidc_count + contacts_by_oidc_count) > 1:
        raise InconsistentSynchronizerStateException(
            f"Multiple users or contacts found for this oidc_id {oidc_id}"
        )
    users_by_email_count = User.objects.filter(email=email).count()
    contacts_by_email_count = Contact.objects.filter(email=email).count()
    if (users_by_email_count + contacts_by_email_count) > 1:
        raise InconsistentSynchronizerStateException(
            f"Multiple users or contacts found for this email {email}"
        )


class AccountSynchronizer(ABC):
    """
    Class that does the synchronization of the account information
    based on the information provided by the synchronizer class
    """

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Should test the connection of the synchronizer and raise an exception
        if there is something wrong.
        """
        pass

    @abstractmethod
    def synchronize_all(self) -> bool:
        """
        Should perform the synchronization itself
        """
        pass

    @abstractmethod
    def build_user_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy User model
        """
        pass

    @abstractmethod
    def build_contact_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Should build a dictionary with the user information based on Daisy Contact model
        """
        pass

    def retrieve_and_update_user_or_contact(
        self,
        oidc_id: str,
        email: Optional[str] = None,
        create_contact_if_not_found: bool = False,
    ) -> Optional[Union[User, Contact]]:
        logger.info(
            f"Retrieve and update or create contact operation started for oidc_id {oidc_id}, email {email}"
        )
        logger.info(
            "Checking for inconsistent state (multiple users or contacts with same oidc_id or email)"
        )

        logger.info("Retrieving user information from external source")
        external_user_information = self.synchronizer_backend.get_external_user_info(
            oidc_id
        )
        logger.info("User details retrieved")
        return self.update_user_or_contact(
            external_user_information, oidc_id, email, create_contact_if_not_found
        )

    def update_user_or_contact(
        self,
        external_user_information: Dict[str, str],
        oidc_id: str,
        email: Optional[str] = None,
        create_contact_if_not_found: bool = False,
    ):
        check_inconsistent_state(oidc_id, email)
        logger.info("No inconsistency found")
        user_dict = self.build_user_dict(external_user_information)
        logger.info(
            f"Trying to find and update corresponding daisy user based on oidc_id {oidc_id}"
        )
        user = update_user(user_info=user_dict, oidc_id=oidc_id)
        if user:
            logger.info(f"Matching user found and updated for daisy user id: {user.id}")
            return user
        logger.info("No matching user found based on oidc_id")
        logger.info(
            f"Trying to find and update corresponding daisy contact based on oidc_id {oidc_id}"
        )
        contact_dict = self.build_contact_dict(external_user_information)
        contact = update_contact(contact_info=contact_dict, oidc_id=oidc_id)
        if contact:
            logger.info(
                f"Matching contact found and updated for daisy contact id: {contact.id}",
            )
            return contact
        logger.info("No matching contact found based on oidc_id")
        if email:
            logger.info(
                f"Trying to find and update corresponding daisy user based on email {email}"
            )
            user = update_user(user_info=user_dict, email=email)
            if user:
                logger.info(
                    f"Matching user found and updated for daisy user id: {user.id}"
                )
                return user
            logger.info("No matching user found based on email")
            logger.info(
                f"Trying to find and update corresponding daisy contact based on email {email}"
            )
            contact = update_contact(contact_info=contact_dict, email=email)
            if contact:
                logger.info(
                    f"Matching contact found and updated for daisy contact id: {contact.id}",
                )
                return contact
        logger.info("No matching contact found based on email")
        if create_contact_if_not_found:
            contact = create_contact(contact_dict)
            logger.info("New contact created")
            return contact
        else:
            logger.info("No matching user or contact found, no contact created neither")
            raise NoUserOrContactFoundInDaisyException(
                "no user or contact found for this oidc_id"
            )

    def retrieve_and_update_user(self, external_id) -> Optional[User]:
        user_info = self.get_user_info(external_id)
        return update_user(user_info, external_id)

    def retrieve_and_update_contact(self, external_id) -> Optional[Contact]:
        contact_info = self.get_contact_info(external_id)
        return update_contact(contact_info, external_id)


class DummySynchronizationBackend(AccountSynchronizationBackend):
    """
    This synchronizer will never report that there is something to change in the accounts
    """

    def __init__(self, config: Dict = None, connect=False) -> None:
        pass

    def test_connection(self) -> bool:
        return True

    def get_list_of_users(self) -> List[Dict]:
        return []

    def get_external_user_info(self, oidc_id: str) -> Dict[str, str]:
        raise NotImplementedError


class DummyAccountSynchronizer(AccountSynchronizer):
    """
    This synchronizer will never change the accounts
    (moreover it will allow to skip passing the synchronizer in the constructor)
    """

    def __init__(self, synchronizer_backend):
        self.synchronizer_backend = synchronizer_backend

    def build_user_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        return {
            "first_name": external_user_information.get(
                "first_name", "FIRST_NAME_MISSING"
            ),
            "last_name": external_user_information.get(
                "last_name", "LAST_NAME_MISSING"
            ),
            "email": external_user_information.get("email"),
            "id": external_user_information.get("id"),
        }

    def build_contact_dict(
        self, external_user_information: Dict[str, str]
    ) -> Dict[str, str]:
        return {
            "first_name": external_user_information.get(
                "first_name", "FIRST_NAME_MISSING"
            ),
            "last_name": external_user_information.get(
                "last_name", "LAST_NAME_MISSING"
            ),
            "email": external_user_information.get("email"),
            "id": external_user_information.get("id"),
        }

    def test_connection(self):
        return True

    def compare(self) -> Tuple[List, List, List]:
        return [], [], []

    def synchronize_all(self) -> bool:
        return True
