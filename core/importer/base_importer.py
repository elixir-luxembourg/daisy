
from core.models import Partner, Contact, ContactType
from core.models import User
from core.utils import DaisyLogger
from django.conf import settings
from core.constants import Groups as GroupConstants
from django.contrib.auth.models import Group


PRINCIPAL_INVESTIGATOR = 'Principal_Investigator'

class BaseImporter:

    logger = DaisyLogger(__name__)

    def process_contacts(self, project_dict):
        local_custodians = []
        local_personnel = []
        external_contacts = []

        home_organisation =  Partner.objects.get(acronym=settings.COMPANY)

        for contact_dict in project_dict.get('contacts', []):
            first_name = contact_dict.get('first_name').strip()
            last_name = contact_dict.get('last_name').strip()
            email = contact_dict.get('email','').strip()
            full_name = "{} {}".format(first_name, last_name)
            role_name = contact_dict.get('role')
            if home_organisation.elu_accession == contact_dict.get('institution').strip():
                user = (User.objects.filter(first_name__icontains=first_name.lower(),
                                            last_name__icontains=last_name.lower()) | User.objects.filter(
                    first_name__icontains=first_name.upper(), last_name__icontains=last_name.upper())).first()
                if user is None:
                    self.logger.warning('no user found for %s an inactive user will be created', full_name)

                    usr_name = first_name.lower() + '.' + last_name.lower()
                    user = User.objects.create(username=usr_name, password='', first_name=first_name, last_name=last_name, is_active=False,
                                               email=email,
                                               )
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
                    affiliation = Partner.objects.get(elu_accession=contact_dict.get('institution'))
                    if affiliation:
                        contact.partners.add(affiliation)
                    contact.save()
                    external_contacts.append(contact)

        return local_custodians, local_personnel, external_contacts

