import json
import sys
import re

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group

from core.constants import Groups as GroupConstants
from core.models import Partner, Contact, ContactType
from core.models import User
from core.utils import DaisyLogger


PRINCIPAL_INVESTIGATOR = 'Principal_Investigator'


class BaseImporter:
    class DateImportException(Exception):
        pass

    logger = DaisyLogger(__name__)

    @property
    def json_schema_validator(self):
        raise NotImplementedError

    def import_json(self, json_string, stop_on_error=False, verbose=False):
        self.logger.info(f'Import ({self.__class__.__name__}) started for file')
        result = True
        json_list = json.loads(json_string)['items']
        self.json_schema_validator.validate_items(json_list, self.logger)
        for item in json_list:
            self.logger.debug(' * Importing item: "{}"...'.format(item.get('name', 'N/A')))
            try:
                self.process_json(item)
            except Exception as e:
                self.logger.error('Import failed')
                self.logger.error(str(e))
                if verbose:
                    import traceback
                    ex = traceback.format_exception(*sys.exc_info())
                    self.logger.error('\n'.join([e for e in ex]))
                if stop_on_error:
                    raise e
                result = False
            self.logger.info('... completed')
        self.logger.info('Import ({}) result for file: {}'.format(self.__class__.__name__, 'success' if result else 'failed'))
        return result

    def process_json(self, import_dict):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")

    def process_contacts(self, contacts_list):
        local_custodians = []
        local_personnel = []
        external_contacts = []
        for contact_dict in contacts_list:
            first_name = contact_dict.get('first_name').strip()
            last_name = contact_dict.get('last_name').strip()
            email = contact_dict.get('email', '').strip()
            full_name = f"{first_name} {last_name}"
            role_name = contact_dict.get('role')
            _is_local_contact = self.is_local_contact(contact_dict)
            if _is_local_contact:
                user = User.objects.filter(first_name__icontains=first_name.lower(),
                                           last_name__icontains=last_name.lower())
                if len(user) > 1:
                    users = User.objects.filter(first_name__icontains=first_name.lower(),
                                                last_name__icontains=last_name.lower(),
                                                email=email)
                    if len(users) != 1:
                        msg = 'Something went wrong - there are two contacts with the same first and last name, and it''s impossible to differentiate them'
                        self.logger.warning(msg, full_name)
                    user = users.first()
                elif len(user) == 1:
                    user = user.first()
                else:
                    user = None
                if user is None:
                    self.logger.warning('No user found for %s - hence an inactive user will be created', full_name)

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
                if role_name == PRINCIPAL_INVESTIGATOR:
                    local_custodians.append(user)
                else:
                    local_personnel.append(user)

            else:
                contact = (Contact.objects.filter(first_name__icontains=first_name.lower(),
                                                  last_name__icontains=last_name.lower()) | Contact.objects.filter(
                    first_name__icontains=first_name.upper(), last_name__icontains=last_name.upper())).first()
                if contact is None:
                    contact_type_pi, _ = ContactType.objects.get_or_create(name=role_name)
                    contact, _ = Contact.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        type=contact_type_pi
                    )
                    affiliations = contact_dict.get('affiliations')
                    for affiliation in affiliations:
                        partner = Partners.objects.filter(name=affiliation)
                        if len(partner):
                            contact.partners.add(partner[0])
                        else:
                            self.logger.warning('no partner found for the affiliation: %s', affiliation)
                    contact.save()
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
            date_str = "{}-{}-{}".format(year, month, day)
            try:
                r = datetime.strptime(date_str, "%Y-%m-%d").date()
                return r
            except (TypeError, ValueError):
                raise self.DateImportException("Couldn't parse the following date: " + str(date_string))
        else:
            raise self.DateImportException("Couldn't parse the following date: " + str(date_string))

    @staticmethod
    def is_local_contact(contact_dict):
        home_organisation = Partner.objects.get(acronym=settings.COMPANY)
        _is_local_contact = home_organisation.name in contact_dict.get("affiliations")
        return _is_local_contact
