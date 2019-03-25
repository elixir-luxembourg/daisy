import json
import sys

from core.exceptions import DatasetImportError
from core.models import Dataset, DataType,  Partner, Project, Contract, ContactType, Contact, PartnerRole, \
    GDPRRole, UseRestriction
from core.models.data_declaration import SubjectCategory, DeidentificationMethod, DataDeclaration, ShareCategory, \
    ConsentStatus
from core.utils import DaisyLogger

logger = DaisyLogger(__name__)


class DatadecsImporter:

    def import_json(self, json_string, stop_on_error=False, verbose=False):
        logger.info('Import started for file')
        result = True
        all_dicts = json.loads(json_string)
        for datadec_dict in all_dicts:
            logger.debug(' * Importing data declaration : "{}"...'.format(datadec_dict.get('title', 'N/A')))
            try:
                self.process_datadec(datadec_dict)
            except Exception as e:
                logger.error('Import failed')
                logger.error(str(e))
                if verbose:
                    import traceback
                    ex = traceback.format_exception(*sys.exc_info())
                    logger.error('\n'.join([e for e in ex]))
                if stop_on_error:
                    raise e
                result = False
            logger.debug("   ... complete!")
        logger.info('Import result for file: {}'.format('success' if result else 'fail'))
        return result

    def process_datadec(self, datadec_dict, **kwargs):
        try:
            title = datadec_dict['title']
        except KeyError:
            raise DatasetImportError(data='Data declaration title missing')

        if 'dataset_obj' not in kwargs:
            try:
                dataset_title = datadec_dict['dataset']
                dataset = Dataset.objects.get(title=dataset_title.strip())
            except KeyError:
                raise DatasetImportError(data='Parent dataset info missing')
            except Dataset.DoesNotExist:
                raise DatasetImportError(data='Parent dataset not found in DB')
        else:
            dataset = kwargs.pop('dataset_obj')
        try:
            datadec = DataDeclaration.objects.get(title=title.strip(), dataset=dataset)
        except DataDeclaration.DoesNotExist:
            datadec = None

        if datadec:
            logger.warning("Data declaration with title '{}' already found. It will be updated.".format(title))
        else:
            datadec = DataDeclaration.objects.create(title=title, dataset=dataset)

        datadec.has_special_subjects = datadec_dict.get('has_special_subjects', False)
        datadec.data_types_notes = datadec_dict.get('data_type_notes', None)
        datadec.deidentification_method = self.process_deidentification_method(datadec_dict)
        datadec.subjects_category = self.process_subjects_category(datadec_dict)
        datadec.special_subjects_description = datadec_dict.get('special_subject_notes', None)
        datadec.other_external_id = datadec_dict.get('other_external_id', None)
        datadec.share_category = self.process_access_category(datadec_dict)
        datadec.consent_status = self.process_constent_status(datadec_dict)
        datadec.comments = datadec_dict.get('source_notes', None)

        if 'data_types' in datadec_dict:
            datadec.data_types_received.set(self.process_datatypes(datadec_dict))

        if 'contract_obj' not in kwargs:
            if 'source_collaboration' in datadec_dict:
                datadec.contract = self.process_source_contract(dataset, datadec_dict)
        else:
            datadec.contract = kwargs.pop('contract_obj')
        if datadec.contract:
            datadec.partner = datadec.contract.partners.first()
        self.process_use_restrictions(datadec, datadec_dict)


        datadec.save()

    def process_datatypes(self, datadec_dict):
        datatypes = []
        for datatype_str in datadec_dict.get('data_types', []):
            datatype_str = datatype_str.strip()
            # TODO Data types is a controlled vocabulaRY we should not create new when importing
            datatype, _ = DataType.objects.get_or_create(name=datatype_str)
            datatypes.append(datatype)
        return datatypes

    def process_deidentification_method(self, datadec_dict):
        deidentification_method_str = datadec_dict.get('de_identification', '')
        try:
            return DeidentificationMethod[deidentification_method_str]
        except KeyError:
            return DeidentificationMethod.pseudonymization

    def process_subjects_category(self, datadec_dict):
        if 'subject_categories' in datadec_dict:
            sub_category_str = datadec_dict.get('subject_categories', '').strip()
            try:
                return SubjectCategory[sub_category_str]
            except KeyError:
                return SubjectCategory.unknown
        else:
            return SubjectCategory.unknown

    def process_source_contract(self, dataset, datadec_dict):

        contract_dict = datadec_dict['source_collaboration']

        try:
            partner_elu = contract_dict['collab_inst']
            if partner_elu is None:
                raise DatasetImportError(f'Partner accession number is NULL!')
            partner = Partner.objects.get(elu_accession=partner_elu.strip())
        except KeyError:
            raise DatasetImportError(f'Contract partner accession number is missing')
        except Partner.DoesNotExist:
            raise DatasetImportError(f'Cannot find institution partner with the elu: {repository}')

        if 'collab_project' not in contract_dict:
            logger.debug(
                ' * Contract project missing! Skipping contract setting for datadeclaration : "{}"...'.format(
                    datadec_dict.get('title', 'N/A')))
            return None
        else:
            # create contract project if it does not exist
            try:
                project = Project.objects.get(acronym=contract_dict['collab_project'].strip())
            except Project.DoesNotExist:
                project = Project.objects.create(
                    acronym=contract_dict['collab_project'].strip()
                )
                project.local_custodians.set(dataset.local_custodians.all())
                project.save()
            try:
                contract = Contract.objects.get(
                    partners_roles__partner=partner,
                    project=project)
            except Contract.DoesNotExist:
                if 'collab_role' in contract_dict:
                    role_str = contract_dict['collab_role']
                    role = GDPRRole[role_str]
                else:
                    role = GDPRRole["joint_controller"]

                contract = Contract.objects.create(
                    project=project,
                )
                contract.company_roles.add(role)
                contract.add_partner_with_role(partner=partner, role=role)
            contract.local_custodians.set(project.local_custodians.all())

            if 'collab_pi' in contract_dict:
                contact_type_pi, _ = ContactType.objects.get_or_create(name="Principal_Investigator")

                contract_pi_str = contract_dict['collab_pi']
                contract_split = contract_pi_str.split()

                first_name = contract_split[0]
                last_name = " ".join(contract_split[1:])
                contact, _ = Contact.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    type=contact_type_pi
                )
                contact.partner = partner
                contact.save()
                partner_role = PartnerRole.objects.filter(contract=contract, partner=partner).first()
                partner_role.contacts.add(contact)
                partner_role.save()

            contract.save()
            return contract

    def process_use_restrictions(self, data_dec, datadec_dict):
        use_restrictions = []
        for user_restriction_dict in datadec_dict['use_restrictions']:
            ga4gh_code = user_restriction_dict['ga4gh_code']
            notes = user_restriction_dict['note']

            use_restriction = UseRestriction.objects.create(data_declaration=data_dec, restriction_class=ga4gh_code, notes=notes)
            use_restrictions.append(use_restriction)
        return use_restrictions

    def process_access_category(self, datadec_dict):
        share_category_str = datadec_dict.get('access_category', '').strip()
        try:
            return ShareCategory[share_category_str]
        except KeyError:
            return None

    def process_constent_status(self, datadec_dict):
        if 'consent_status' in datadec_dict:
            consent_status_str = datadec_dict.get('consent_status', '').strip()
            try:
                return ConsentStatus[consent_status_str]
            except KeyError:
                return ConsentStatus.unknown
        else:
            return ConsentStatus.unknown
