import json
import sys
import re

from datetime import datetime
from typing import Dict, List

from django.conf import settings
from django.contrib.auth.models import Group

from core.constants import Groups as GroupConstants
from core.models import Partner, Contact, ContactType, User
from core.utils import DaisyLogger


PRINCIPAL_INVESTIGATOR = 'Principal_Investigator'


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

    @property
    def json_schema_validator(self):
        """
        This validator will be used against the imported data
        """
        raise NotImplementedError('You must implement `json_schema_validator` in your importer class')

    @property
    def json_schema_uri(self):
        """
        This attribute is used for detecting whether the importer can handle given json
        """
        raise NotImplementedError('You must implement `json_schema_uri` in your importer class')

    def can_process_json(self, json_string: str) -> bool:
        """
        Checks whether the imported JSON has the same "$schema" URI as the importer class (in `json_schema_uri` property)
        """
        try:
            object = json.loads(json_string)
            return self.can_process_object(object)
        except:
            message = f'Couldn\'t check if the imported object has same "$schema" as the importer ({self.__class__.__name__}: {self.json_schema_uri}) - something went wrong while parsing the file'
            self.logger.warn(message)
            return False

    def can_process_object(self, json_object: Dict) -> bool:
        """
        Checks whether the object has the same "$schema" URI as the importer class (in `json_schema_uri` property)
        """
        if not json_object.get('$schema', False):
            self.logger.debug('The imported object has no "$schema" attribute')
            return False
        if self.json_schema_uri == json_object.get('$schema'):
            message = f'The imported object has the same "$schema" ({self.json_schema_uri}) as the importer ({self.__class__.__name__})'
            self.logger.debug(message)
            return True
        schema_name = json_object.get('$schema')
        message = f'The imported object has different "$schema" ({schema_name}) than the importer ({self.__class__.__name__}: {self.json_schema_uri})'
        self.logger.debug(message)
        return False

    def import_json_file(self, path_to_the_file: str, stop_on_error=False, verbose=False, validate=True) -> bool:
        """
        Opens, loads and imports a JSON file.
        """
        self.logger.info(f'Opening the file: {path_to_the_file}')
        with open(path_to_the_file, encoding='utf-8') as json_file:
            json_file_contents = json_file.read()
            result = self.import_json(json_file_contents, stop_on_error, verbose)
            self.logger.info(f'Successfully completed import for the file: {path_to_the_file}')
            return result

    def import_json(self, json_string: str, stop_on_error=False, verbose=False, validate=True) -> bool:
        result = True
        importer_class_name = self.__class__.__name__
        self.logger.info(f'Attempting to use "{importer_class_name}" to parse and import the JSON')
        json_list = json.loads(json_string)['items']
        result = self.import_object_list(json_list, stop_on_error, verbose)
        status = 'success' if result else 'failed'
        self.logger.info(f'Import ({importer_class_name}) result: {status}')
        return result

    def import_object_list(self, json_list: List[Dict], stop_on_error=False, verbose=False, validate=True) -> bool:
        """
        Validates and imports a list of objects.
        """
        result = True
        if validate:
            validator_name = self.json_schema_validator.__class__.__name__
            self.logger.debug(f'Validating the file with "{validator_name}" against JSON schema...')
            self.json_schema_validator.validate_items(json_list, self.logger)
            self.logger.debug('...JSON schema is OK!')
        else:
            self.logger.debug(f'Proceeding without using the validation')
        count = len(json_list)
        verb = 'are' if count > 1 else 'is'
        self.logger.debug(f'There {verb} {count} object(s) to be imported. Starting the process...')
        for item in json_list:
            result = self.import_object(item, stop_on_error, verbose) and result
        self.logger.debug('Finished importing the object(s)')
        return result

    def import_object(self, item: Dict, stop_on_error=False, verbose=False):
        """
        Tries to import a single object
        """
        item_name = item.get('name', 'N/A').encode('utf-8')
        self.logger.debug(f'Trying to import item: "{item_name}"')
        try:
            result = self.process_json(item)
        except Exception as e:
            self.logger.error('Import failed: ')
            self.logger.error(str(e))
            if verbose:
                import traceback
                ex = traceback.format_exception(*sys.exc_info())
                self.logger.error('\n'.join([e for e in ex]))
            if stop_on_error:
                raise e
            result = False
        self.logger.debug(f'Successfully imported item: {item_name}')
        return result

    def process_json(self, import_dict):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")

    def process_contacts(self, contacts_list: List[Dict]):
        if not isinstance(contacts_list, list):
            self.logger.warn('Contact list is not a list... Please check the imported file.')
            return [], [], []
        
        local_custodians = []
        local_personnel = []
        external_contacts = []
        for contact_dict in contacts_list:
            first_name = contact_dict.get('first_name').strip()
            last_name = contact_dict.get('last_name').strip()
            email = contact_dict.get('email', '').strip()
            role_name = self.validate_contact_type(contact_dict.get('role'))
            affiliations = contact_dict.get('affiliations', [])
            if self.is_local_contact(contact_dict):
                user = self.process_local_contact(first_name, last_name, email, role_name, affiliations)
                if role_name == PRINCIPAL_INVESTIGATOR:
                    local_custodians.append(user)
                else:
                    local_personnel.append(user)

            else:
                contact = self.process_external_contact(first_name, last_name, email, role_name, affiliations)
                external_contacts.append(contact)

        return local_custodians, local_personnel, external_contacts

    @staticmethod
    def process_partner(partner_name):
        partner, _ = Partner.objects.get_or_create(name=partner_name)
        return partner

    def process_date(self, date_string):
        regex = r'([0-9]{4})-([0-9]{2})-([0-9]{2})'
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
                raise self.DateImportException(f"Couldn't parse the following date: {str(date_string)}")
        else:
            raise self.DateImportException(f"Couldn't parse the following date: {str(date_string)}")

    @staticmethod
    def is_local_contact(contact_dict):
        home_organisation = Partner.objects.get(acronym=settings.COMPANY)
        _is_local_contact = home_organisation.name in contact_dict.get("affiliations") or home_organisation.acronym in contact_dict.get("affiliations")
        return _is_local_contact

    def validate_contact_type(self, contact_type):
        try:
            contact_type_obj = ContactType.objects.get(name=contact_type)
        except ContactType.DoesNotExist:
            self.logger.warning(f'Unknown contact type: {contact_type}. Setting to "Other".')
            contact_type = 'Other'
        return contact_type

    def process_local_contact(self, first_name, last_name, email, role_name, affiliations):
        user = User.objects.filter(first_name__icontains=first_name,last_name__icontains=last_name)
        if len(user) > 1:
            users = User.objects.filter(first_name__icontains=first_name,
                                        last_name__icontains=last_name,
                                        email=email)
            if len(users) != 1:
                msg = 'Something went wrong - there are two contacts with the same first and last name, and it''s impossible to differentiate them'
                self.logger.warning(msg)
            user = users.first()
        elif len(user) == 1:
            user = user.first()
        else:
            user = None
        if user is None:
            self.logger.warning(f"No user found for '{first_name} {last_name}' - hence an inactive user will be created")

            usr_name = first_name.lower() + '.' + last_name.lower()
            user = User.objects.create(username=usr_name,
                                        password='',
                                        first_name=first_name,
                                        last_name=last_name,
                                        is_active=False,
                                        email=email)
            user.staff = True

            if role_name == PRINCIPAL_INVESTIGATOR:
                g = Group.objects.get(name=GroupConstants.VIP.value)
                user.groups.add(g)
            user.save()
        return user

    def process_external_contact(self, first_name, last_name, email, role_name, affiliations):
        contact = (
            Contact.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name,
                partners__name__in=affiliations) |
            Contact.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name,
                partners__acronym__in=affiliations)
                ).first()
        if contact is None:
            contact = Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                type=ContactType.objects.get(name=role_name)
            )
            for affiliation in affiliations:
                partner = Partner.objects.filter(name=affiliation)
                if len(partner):
                    contact.partners.add(partner[0])
                else:
                    self.logger.warning(f"Cannot link contact '{first_name} {last_name}' to partner. No partner found for the affiliation: {affiliation}")
            contact.save()
        return contact

