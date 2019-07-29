import logging
import re
from datetime import datetime
from json import loads

from core.models import Partner, Project, Publication, Contact, ContactType
from core.models import User


from django.conf import settings

PRINCIPAL_INVESTIGATOR = 'Principal_Investigator'

logger = logging.getLogger(__name__)


from core.constants import Groups as GroupConstants
from django.contrib.auth.models import Group

class ProjectsImporter:
    """
    `ProjectsImporter`, should be able to fill the database with projects' information, based on JSON file
    complying to the schema in:
     https://git-r3lab.uni.lu/pinar.alper/metadata-tools/blob/master/metadata_tools/resources/elu-study.json

    Usage example:
        def import_projects():
            with open("projects.json", "r") as file_with_projects:
                importer = ProjectsImporter()
                importer.import_json(file_with_projects.read())
    """


    class DateImportException(Exception):
        pass

    def import_json(self, json_string, stop_on_error=False):
        try:
            logger.info('Import started"')
            all_information = loads(json_string)
            logger.debug('Import started"')
            for project in all_information:
                logger.debug(' * Importing project: "{}"...'.format(project.get('acronym', "N/A")))
                self.process_project(project)
                logger.debug("   ... success!")
            logger.info('Import succeeded"')
        except Exception as e:
            logger.error('Import failed"')
            logger.error(str(e))
            if stop_on_error:
                raise e

    def process_project(self, project_dict):

        publications = [self.process_publication(publication_dict)
                        for publication_dict
                        in project_dict.get('publications', [])]

        title = project_dict.get('title', "N/A")
        description = project_dict.get('description', None)
        has_cner = project_dict.get('has_national_ethics_approval', False)
        has_erp = project_dict.get('has_institutional_ethics_approval', False)
        cner_notes = project_dict.get('national_ethics_approval_notes', None)
        erp_notes = project_dict.get('institutional_ethics_approval_notes', None)
        acronym = project_dict.get('acronym')
        project = Project.objects.filter(acronym=acronym).first()
        if project is None:
            project = Project.objects.create(acronym=acronym,
                                             title=title,
                                             description=description,
                                             has_cner=has_cner,
                                             has_erp=has_erp,
                                             cner_notes=cner_notes,
                                             erp_notes=erp_notes
                                             )
        else:
            logger.warning("Project with acronym '{}' already found. It will be updated.".format(acronym))
            project.title = title
            project.description = description
            project.has_cner = has_cner
            project.has_erp = has_erp
            project.cner_notes = cner_notes
            project.erp_notes = erp_notes

        try:
            if 'start_date' in project_dict and len(project_dict.get('start_date')) > 0:
                project.start_date = self.process_date(project_dict.get('start_date'))
        except ProjectsImporter.DateImportException:
            message = "\tCouldn't import the 'start_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + 'Was: "{}". '.format(project_dict.get('start_date'))
            message = message + "Continuing with empty value."
            logger.warning(message)

        try:
            if 'end_date' in project_dict and len(project_dict.get('end_date')) > 0:
                project.end_date = self.process_date(project_dict.get('end_date'))
        except ProjectsImporter.DateImportException:
            message = "\tCouldn't import the 'end_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + 'Was: "{}". '.format(project_dict.get('end_date'))
            message = message + "Continuing with empty value."
            logger.warning(message)

        project.save()

        local_custodians, local_personnel, external_contacts = self.process_contacts(project_dict)

        if local_personnel:
            project.company_personnel.set(local_personnel, clear=True)

        if local_custodians:
            project.local_custodians.set(local_custodians, clear=True)

        for publication in publications:
            project.publications.add(publication)

        project.updated = True
        project.save()
        for local_custodian in local_custodians:
            local_custodian.assign_permissions_to_dataset(project)


    def process_contacts(self, project_dict):
        local_custodians = []
        local_personnel = []
        external_contacts = []

        home_organisation =  Partner.objects.get(acronym=settings.COMPANY)

        for contact_dict in project_dict.get('contacts', []):
            first_name = contact_dict.get('first_name').strip()
            last_name = contact_dict.get('last_name').strip()
            full_name = "{} {}".format(first_name, last_name)
            role_name = contact_dict.get('role')
            if home_organisation.elu_accession == contact_dict.get('institution').strip():
                user = (User.objects.filter(first_name__icontains=first_name.lower(),
                                                    last_name__icontains=last_name.lower()) | User.objects.filter(
                            first_name__icontains=first_name.upper(), last_name__icontains=last_name.upper())).first()
                if user is None:
                    logger.warning('no user found for %s an inactive user will be created', full_name)

                    usr_name = first_name.lower() + '.' + last_name.lower()
                    user = User.objects.create(username=usr_name, password='', first_name=first_name, last_name=last_name, is_active=False,
                                               email='inactive.user@uni.lu',
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
                    contact = Contact.objects.create(first_name=first_name, last_name=last_name )
                    contact.type =  ContactType.objects.get_or_create(name=role_name)
                    affiliation = Partner.objects.get(elu_accession=contact_dict.get('institution'))
                    if affiliation:
                        contact.partners.add(affiliation)
                    contact.save()
                    external_contacts.append(contact)

        return local_custodians, local_personnel, external_contacts




    @staticmethod
    def process_partner(partner_string):
        partner, _ = Partner.objects.get_or_create(name=partner_string)
        return partner


    @staticmethod
    def process_publication(publication_dict):

        publication = Publication.objects.create(citation=publication_dict.get('citation_string'))
        if 'doi' in publication_dict:
            publication.doi = publication_dict.get('doi')
            publication.save()


        return publication


    @staticmethod
    def process_date(date_string):
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
                raise ProjectsImporter.DateImportException("Couldn't parse the following date: " + str(date_string))
        else:
            raise ProjectsImporter.DateImportException("Couldn't parse the following date: " + str(date_string))
