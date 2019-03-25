import json
import sys

from django.utils.datetime_safe import datetime

from core.exceptions import DatasetImportError
from core.importer.datadecs_importer import DatadecsImporter
from core.importer.datasets_importer import DatasetsImporter
from core.models import Contact, Dataset, Partner, Project, ContactType, GDPRRole
from core.models.contract import Contract
from core.utils import DaisyLogger
from .projects_importer import ProjectsImporter

logger = DaisyLogger(__name__)


class DishSubmissionImporter:
    """
    `DishSubmissionImporter`, parse  json export of the Data Submission System
    and create relevant  Dataset, Collaboration, (external Project) and DataDeclaration records in DAISY
    """

    class DateImportException(Exception):
        pass

    def __init__(self, elixir_project_name):
        self.elixir_project_name = elixir_project_name

    def import_json(self, json_string, stop_on_error=False, verbose=False):
        try:
            logger.info('Import started')
            submission_dict = json.loads(json_string)
            logger.debug(' * Importing Data Declaration: "{}"...'.format(submission_dict['title']))

            if self.is_elixir_submission(submission_dict):
                project = Project.objects.filter(acronym=self.elixir_project_name).first()

            dataset = self.process_submission_as_dataset(submission_dict, project)
            contract = self.process_submission_as_contract(submission_dict, project)
            datadec_dicts = submission_dict.get('datadecs', [])
            importer = DatadecsImporter()
            for datadec_dict in datadec_dicts:
                kwargs = {}
                kwargs['dataset_obj'] = dataset
                if contract:
                    kwargs['contract_obj'] = contract
                importer.process_datadec(datadec_dict, **kwargs)

            for study_dict in submission_dict.get('studies', []):
                study = self.process_study(study_dict)



        except Exception as e:
            logger.error('Import failed')
            logger.error(str(e))
            if verbose:
                import traceback
                ex = traceback.format_exception(*sys.exc_info())
                logger.error('\n'.join([e for e in ex]))
            if stop_on_error:
                raise e
            return False
        return True

    def process_submission_as_contract(self, submission_dict, project):
        try:
            partner_accession = submission_dict['submitting_institution']
        except KeyError:
            raise DatasetImportError(data='Submitting institute info missing. Aborting import!')

        try:
            partner = Partner.objects.get(elu_accession=partner_accession)
        except Partner.DoesNotExist:
            raise DatasetImportError(
                data='Partner institute with accession {} not found in DB. Aborting import.'.format(partner_accession))

        if self.is_elixir_submission(submission_dict):
            try:
                contract = Contract.objects.get(project=project, partners_roles__partner=partner)
            except Contract.DoesNotExist:
                contract = Contract.objects.create(
                    project=project,
                )
                contract.company_roles.add(GDPRRole["joint_controller"])
                contract.add_partner_with_role(partner, GDPRRole["joint_controller"])
                contract.local_custodians.set(project.local_custodians.all())
                contract.save()
        return contract

    def process_study(self, study_dict):
        try:
            title = study_dict['title']
        except KeyError:
            raise DatasetImportError(data='study without title')

        description = study_dict.get('description', None)
        ethics_approval_exists = study_dict.get('ethics_approval_exists', False)
        ethics_notes = "The submitter confirms that an ethics approval exists for the data collection, sharing and \
        the purposes for which the data is shared." if ethics_approval_exists else None

        existing_project = Project.objects.filter(title=title).first()
        if existing_project is not None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.warning(
                "Project with title '{}' already found. It will be imported again with timestamp {}.".format(title,
                                                                                                             timestamp))
            title = title + timestamp

        project = Project.objects.create(title=title,
                                         description=description,
                                         has_cner=ethics_approval_exists,
                                         cner_notes=ethics_notes
                                         )
        contacts = self.process_external_contacts(study_dict.get('contacts', []))

        if contacts:
            project.contacts.set(contacts)
            project.save()

        # study_types = self.process_studytypes(study_dict)
        # if study_types:
        #     project.study_types.set(study_types)
        #     project.save()

        return project

    @staticmethod
    def process_role(role_string):
        role, _ = ContactType.objects.get_or_create(name=role_string.strip())
        return role

    # def process_studytypes(self, study_dict):
    #     studytypes = []
    #     for studytype_str in study_dict.get('study_types', []):
    #         studytype_str = studytype_str.strip().capitalize().replace('_', ' ')
    #         studytype, _ = StudyType.objects.get_or_create(name=studytype_str)
    #         studytypes.append(studytype)
    #     return studytypes

    def process_external_contacts(self, contact_dicts):
        contacts = []
        for contact_dict in contact_dicts:
            if 'role' in contact_dict:
                role = self.process_role(contact_dict.get('role'))

            partner = ProjectsImporter.process_partner(contact_dict.get('institution'))
            contact, _ = Contact.objects.get_or_create(first_name=contact_dict.get('first_name').strip(),
                                                       last_name=contact_dict.get('last_name').strip(),
                                                       email=contact_dict.get('email').strip(),
                                                       type=role)
            contact.partners.set([partner])
            contact.save()
            contacts.append(contact)

        return contacts

    def is_elixir_submission(self, submission_dict):
        return submission_dict['scope'] == 'e'

    def process_submission_as_dataset(self, submission_dict, project):
        try:
            elu_accession = submission_dict['elu_accession']
        except KeyError:
            raise DatasetImportError(data='submission without accession number')

        dataset = Dataset.objects.filter(title=elu_accession.strip()).first()
        if dataset is not None:
            logger.warning(
                "Dataset with title '{}' already found. It will be updated.".format(elu_accession.strip()))
        else:

            dataset = Dataset.objects.create(title=elu_accession.strip())

        dataset.project = project

        created_on_str = submission_dict['created_on']
        title = submission_dict['title']
        scope_str = 'Elixir' if submission_dict['scope'] == 'e' else 'LCSB Collaboration'
        local_project_str = submission_dict.get('local_project', '')
        dataset.comments = "ELU Accession: {}\nTitle: {}\nCreated On: {}\nScope: {}\nSubmitted to Project: {}".format(
            elu_accession, title, created_on_str, scope_str, local_project_str)

        local_custodians = DatasetsImporter.process_local_custodians(submission_dict)
        if local_custodians:
            dataset.local_custodians.set(local_custodians)
        dataset.save()
        return dataset
