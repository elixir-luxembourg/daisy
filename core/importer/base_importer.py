import json
import sys
import re

from datetime import datetime
from typing import Dict, List

from django.conf import settings

from core.lcsb.oidc import KeycloakBackend, get_keycloak_config_from_settings
from core.models import Partner, Contact, ContactType, User
from core.synchronizers import get_contact, create_user
from core.utils import DaisyLogger, normalized_email, records_with_email

PRINCIPAL_INVESTIGATOR = "Principal_Investigator"


class BaseImporter:
    """
    Abstract base class for an importer.
    Provides common functions for opening/parsing/validating JSON files.

    Take a look on `ProjectsImporter` or `DatasetsImporter` for information
    how an implementation should look like.
    """

    class DateImportException(Exception):
        pass

    logger = DaisyLogger(__name__)

    def __init__(
        self,
        publish_on_import=False,
        exit_on_error=False,
        verbose=False,
        validate=True,
        skip_on_exist=True,
    ):
        self.verbose = verbose
        self.publish_on_import = publish_on_import
        self.exit_on_error = exit_on_error
        self.validate = validate
        self.skip_on_exist = skip_on_exist
        # one connection per import, process_contacts asks Keycloak per contact
        self._keycloak_backend = None

    @property
    def json_schema_validator(self):
        """
        This validator will be used against the imported data
        """
        raise NotImplementedError(
            "You must implement `json_schema_validator` in your importer class"
        )

    @property
    def json_schema_uri(self):
        """
        This attribute is used for detecting whether the importer can handle given json
        """
        raise NotImplementedError(
            "You must implement `json_schema_uri` in your importer class"
        )

    def can_process_json(self, json_string: str) -> bool:
        """
        Checks whether the imported JSON has the same "$schema" URI as the importer class (in `json_schema_uri` property)
        """
        try:
            object = json.loads(json_string)
            return self.can_process_object(object)
        except:
            message = f'Couldn\'t check if the imported object has same "$schema" as the importer ({self.__class__.__name__}: {self.json_schema_uri}) - something went wrong while parsing the file'
            self.logger.warning(message)
            return False

    def can_process_object(self, json_object: Dict) -> bool:
        """
        Checks whether the object has the same "$schema" URI as the importer class (in `json_schema_uri` property)
        """
        if not json_object.get("$schema", False):
            self.logger.debug('The imported object has no "$schema" attribute')
            return False
        if self.json_schema_uri == json_object.get("$schema"):
            message = f'The imported object has the same "$schema" ({self.json_schema_uri}) as the importer ({self.__class__.__name__})'
            self.logger.debug(message)
            return True
        schema_name = json_object.get("$schema")
        message = f'The imported object has different "$schema" ({schema_name}) than the importer ({self.__class__.__name__}: {self.json_schema_uri})'
        self.logger.debug(message)
        return False

    def import_json_file(self, path_to_the_file: str) -> bool:
        """
        Opens, loads and imports a JSON file.
        """
        self.logger.info(f"Opening the file: {path_to_the_file}")
        with open(path_to_the_file, encoding="utf-8") as json_file:
            json_file_contents = json_file.read()
            result = self.import_json(json_file_contents)
            self.logger.info(
                f"Successfully completed import for the file: {path_to_the_file}"
            )
            return result

    def import_json(self, json_string: str) -> bool:
        result = True
        importer_class_name = self.__class__.__name__
        self.logger.info(
            f'Attempting to use "{importer_class_name}" to parse and import the JSON'
        )
        json_list = json.loads(json_string)["items"]
        result = self.import_object_list(json_list)
        status = "success" if result else "failed"
        self.logger.info(f"Import ({importer_class_name}) result: {status}")
        return result

    def import_object_list(self, json_list: List[Dict]) -> bool:
        """
        Validates and imports a list of objects.
        """
        result = True
        if self.validate:
            validator_name = self.json_schema_validator.__class__.__name__
            self.logger.debug(
                f'Validating the file with "{validator_name}" against JSON schema...'
            )
            self.json_schema_validator.validate_items(json_list, self.logger)
            self.logger.debug("...JSON schema is OK!")
        else:
            self.logger.debug(f"Proceeding without using the validation")
        count = len(json_list)
        verb = "are" if count > 1 else "is"
        self.logger.debug(
            f"There {verb} {count} object(s) to be imported. Starting the process..."
        )
        for item in json_list:
            result = self.import_object(item) and result
        self.logger.debug("Finished importing the object(s)")
        return result

    def import_object(self, item: Dict):
        """
        Tries to import a single object
        """
        item_name = item.get("name", "N/A").encode("utf-8")
        self.logger.debug(f'Trying to import item: "{item_name}"')
        try:
            result = self.process_json(item)
        except Exception as e:
            self.logger.error("Import failed: ")
            self.logger.error(str(e))
            if self.verbose:
                import traceback

                ex = traceback.format_exception(*sys.exc_info())
                self.logger.error("\n".join([e for e in ex]))
            if self.exit_on_error:
                raise e
            result = False

        return result

    def process_json(self, import_dict):
        raise NotImplementedError(
            "Abstract method: Implement this method in the child class."
        )

    def publish_object(self, object) -> bool:
        try:
            object.publish(save=True)
            result = True
        except AttributeError as e:
            self.logger.warning(
                f"Publishing this type of entity ({object._meta.object_name}) is not implemented - item is not published."
            )
            result = False
        return result

    def process_contacts(self, contacts_list: List[Dict]):
        """
        Resolve every contact of an import file: a DAISY user, else a Keycloak account, which
        becomes a user, else a contact.
        Keycloak decides who is a user, because an account means the person can log in. The
        affiliation of the file does not decide it.
        """
        if not isinstance(contacts_list, list):
            self.logger.warning(
                "Contact list is not a list... Please check the imported file."
            )
            return [], [], []

        local_custodians = []
        local_personnel = []
        external_contacts = []
        for contact_dict in contacts_list:
            first_name = contact_dict.get("first_name").strip()
            last_name = contact_dict.get("last_name").strip()
            email = normalized_email(contact_dict.get("email", ""))
            role_name = self.validate_contact_type(contact_dict.get("role"))
            # the key can be present and null
            affiliations = contact_dict.get("affiliations") or []

            user = self.find_user(email, first_name, last_name)
            if user is None:
                user = self.user_from_keycloak(email)
            if user is not None:
                if role_name == PRINCIPAL_INVESTIGATOR:
                    local_custodians.append(user)
                else:
                    local_personnel.append(user)
            else:
                contact = self.process_external_contact(
                    first_name, last_name, email, role_name, affiliations
                )
                external_contacts.append(contact)

        return local_custodians, local_personnel, external_contacts

    def find_user(self, email, first_name, last_name):
        """
        The DAISY user of a contact: by email when the email names exactly one user, by name
        otherwise, because an import file can give one email to several contacts.
        An inactive user is never reused: it is a leaver, or a placeholder of an older import,
        and a login cannot activate a stored row.
        """
        users = User.objects.filter(is_active=True)
        by_email = records_with_email(users, email)
        if len(by_email) == 1:
            return by_email[0]

        # TODO: a name is not an identity, Keycloak is the only reliable check of a local person.
        # Dropping this branch sends the case to user_from_keycloak(), and it changes
        # test_an_active_user_is_reused and every import on an instance without Keycloak.
        by_name = list(
            users.filter(
                first_name__icontains=first_name, last_name__icontains=last_name
            )
        )
        if len(by_name) == 1:
            return by_name[0]
        if len(by_name) > 1:
            by_name_and_email = [
                user for user in by_name if normalized_email(user.email) == email
            ]
            if len(by_name_and_email) == 1:
                return by_name_and_email[0]
            self.logger.warning(
                f"Several users are named '{first_name} {last_name}' and the email does not "
                f"tell them apart, the import asks Keycloak"
            )
        return None

    def user_from_keycloak(self, email):
        """
        The user of the Keycloak account of that email, created when DAISY does not hold it yet.
        Every account of the email becomes a user, as the nightly import does, and the first one
        is the user of this contact. No account means the person is a contact.
        """
        users = []
        for account in self.keycloak_accounts(email):
            contact = get_contact(account.id)
            if contact:
                # a contact never stops a user, but its access rows need a migration
                self.logger.warning(
                    f"Contact {contact.pk} holds the Keycloak subject {account.id}"
                )
            user = User.objects.filter(oidc_id=account.id).first()
            users.append(user or create_user(account))

        if len(users) > 1:
            self.logger.warning(
                f"Several Keycloak accounts for {email}, the import uses {users[0].username}"
            )
        return users[0] if users else None

    def keycloak_accounts(self, email):
        """
        The verified Keycloak accounts of an email. Without the integration, and when Keycloak
        does not answer, it gives nothing: the person becomes a contact and the import goes on.
        """
        if not email or not getattr(settings, "KEYCLOAK_INTEGRATION", False):
            return []
        try:
            if self._keycloak_backend is None:
                self._keycloak_backend = KeycloakBackend(
                    get_keycloak_config_from_settings()
                )
            return self._keycloak_backend.get_users_by_email(email)
        except Exception as exception:
            self.logger.error(
                f"Keycloak does not answer for {email} ({exception}), "
                f"the import treats this person as a contact"
            )
            return []

    @staticmethod
    def process_partner(partner_name):
        partner, _ = Partner.objects.get_or_create(name=partner_name)
        return partner

    def process_date(self, date_string):
        regex = r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
        match = re.match(regex, date_string, re.M | re.I)
        if match:
            year = match.group(1)
            month = match.group(2)
            day = match.group(3)
            date_str = f"{year}-{month}-{day}"
            try:
                r = datetime.strptime(date_str, "%Y-%m-%d").date()
                return r
            except (TypeError, ValueError):
                raise self.DateImportException(
                    f"Couldn't parse the following date: {str(date_string)}"
                )
        else:
            raise self.DateImportException(
                f"Couldn't parse the following date: {str(date_string)}"
            )

    def validate_contact_type(self, contact_type):
        try:
            contact_type_obj = ContactType.objects.get(name=contact_type)
        except ContactType.DoesNotExist:
            self.logger.warning(
                f'Unknown contact type: {contact_type}. Setting to "Other".'
            )
            contact_type = "Other"
        return contact_type

    def process_external_contact(
        self, first_name, last_name, email, role_name, affiliations
    ):
        contact = (
            Contact.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name,
                partners__name__in=affiliations,
            )
            | Contact.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name,
                partners__acronym__in=affiliations,
            )
        ).first()
        if contact is None:
            contact = Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                type=ContactType.objects.get(name=role_name),
            )
            for affiliation in affiliations:
                partner = Partner.objects.filter(
                    name=affiliation
                ) | Partner.objects.filter(acronym=affiliation)
                if len(partner):
                    contact.partners.add(partner[0])
                else:
                    self.logger.warning(
                        f"Cannot link contact '{first_name} {last_name}' to partner. No partner found for the affiliation: {affiliation}"
                    )
            contact.save()
        return contact
