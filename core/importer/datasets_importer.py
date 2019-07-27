import json
import sys

from core.exceptions import DatasetImportError
from core.models import Dataset, Project, StorageResource, User, Contract, Partner, GDPRRole
from core.models.access import Access
from core.models.share import Share
from core.models.storage_location import StorageLocationCategory, DataLocation
from core.utils import DaisyLogger
from core.constants import Groups as GroupConstants
from django.contrib.auth.models import Group

logger = DaisyLogger(__name__)


class DatasetsImporter:
    """
    `DatasetsImporter`, parse json representation of a set of datasets and store them in the database
    """

    class DateImportException(Exception):
        pass

    def import_json(self, json_string, stop_on_error=False, verbose=False):
        logger.info('Import started for file')
        result = True
        dataset_list = json.loads(json_string)
        for dataset in dataset_list:
            logger.debug(' * Importing dataset: "{}"...'.format(dataset.get('title', 'N/A')))
            try:
                self.process_dataset(dataset)
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
            logger.info('... completed')
        logger.info('Import result for file: {}'.format('success' if result else 'fail'))
        return result

    def process_dataset(self, dataset_dict):
        try:
            title = dataset_dict['title']
        except KeyError:
            raise DatasetImportError(data='dataset without title')

        title = title.strip()

        try:
            dataset = Dataset.objects.get(title=title)
        except Dataset.DoesNotExist:
            dataset = None

        if dataset:
            logger.warning("Dataset with title '{}' already found. It will be updated.".format(title))
        else:
            dataset = Dataset.objects.create(title=title)

        if 'project' in dataset_dict:
            dataset.project = self.process_project(dataset_dict['project'])

        dataset.sensitivity = dataset_dict.get('sensitivity', None)

        local_custodians = self.process_local_custodians(dataset_dict)
        if local_custodians:
            dataset.local_custodians.set(local_custodians)

        data_locations = self.process_data_locations(dataset, dataset_dict)
        if data_locations:
            dataset.data_locations.set(data_locations, bulk=False)

        # users_with_access = self.process_user_acl(storage_location_dict)
        # if users_with_access:
        #     dl.users_with_access.set(users_with_access, bulk=False)
        # if 'storage_acl_notes' in storage_location_dict:
        #     dl.access_notes = storage_location_dict['storage_acl_notes']

        shares = self.process_shares(dataset_dict, dataset)
        if shares:
            dataset.shares.set(shares, bulk=False)

        dataset.save()

    @staticmethod
    def process_local_custodians(dataset_dict):
        result = []

        local_custodians = dataset_dict.get('local_custodian', [])

        for local_custodian in local_custodians:
            custodian_str_strip = local_custodian.strip()
            user = (User.objects.filter(full_name__icontains=custodian_str_strip.lower()) | User.objects.filter(
                full_name__icontains=custodian_str_strip.upper())).first()
            if user is None:
                names = custodian_str_strip.split(maxsplit=1)

                if len(names) == 2:
                    logger.warning('no user found for %s and inactive user will be created', custodian_str_strip)
                    usr_name = names[0].strip().lower() + '.' + names[1].strip().lower()
                    user = User.objects.create(username=usr_name, password='', first_name=names[0], last_name=names[1],is_active=False,
                                               email='inactive.user@uni.lu',
                                               )
                    user.staff = True
                    g = Group.objects.get(name=GroupConstants.VIP.value)
                    user.groups.add(g)
                    user.save()
                    result.append(user)

            else:
                result.append(user)
        return result

    def process_project(self, project_name):
        try:
            project = Project.objects.get(acronym=project_name.strip())
        except Project.DoesNotExist:
            project = Project.objects.create(
                acronym=project_name.strip()
            )
        return project

    def process_data_locations(self, dataset, dataset_dict):
        data_locations = []
        backend_mapping = {
            'aspera': 'lcsb-aspera',
            'atlas': 'atlas-server',
            'atlas_personal': 'atlas-server',
            'atlas_project': 'atlas-server',
            'hpc_backup_gaia': 'gaia-cluster',
            'hpc_gaia_home': 'gaia-cluster',
            'hpc_gaia_project': 'gaia-cluster',
            'hpc_gaia_work': 'gaia-cluster',
            'hpc_isilon': 'hpc-isilon',
            'lcsb_desktop': 'uni-desktop',
            'external storage  (e.g. hard disk, dvd)': 'external-device',
            'lcsb_group_server': 'group-server',
            'lcsb_laptop': 'uni-laptop',
            'owncloud': 'lcsb-owncloud',
            'personal_laptop': 'personal-laptop',
            'sample-storage': 'sample-storage',
            'other': 'other'
        }
        if 'storage_locations' in dataset_dict:

            for storage_location_dict in dataset_dict['storage_locations']:
                backend_name = storage_location_dict['storage_resource'].lower().strip()
                backend_name = backend_mapping.get(backend_name, backend_name)
                if not backend_name:
                    raise DatasetImportError(data=f'Not a proper backend name: "{backend_name}".')
                try:
                    backend = StorageResource.objects.get(slug=backend_name)
                except StorageResource.DoesNotExist:
                    raise DatasetImportError(data=f'Cannot find StorageResource with slug: "{backend_name}".')
                category = self.process_category(storage_location_dict)
                acl_policy_description = self.process_acl_info(storage_location_dict)
                #DLCLazz = backend.get_location_class()

                location_delimeted = '\n'.join(storage_location_dict['locations'])

                dl = DataLocation.objects.create(
                    category=category,
                    backend=backend,
                    dataset=dataset,
                    **{'location_description': location_delimeted}
                )
                master_locations = DataLocation.objects.filter(category=StorageLocationCategory.master, dataset=dataset)

                if acl_policy_description:
                    acc = Access.objects.create(
                        dataset=dataset,
                        access_notes=acl_policy_description
                    )
                    acc.defined_on_locations.set(master_locations)
                    acc.save()
                data_locations.append(dl)
        return data_locations

    def process_user_acl(self, storage_location_dict):
        storage_acl_info = storage_location_dict.get("storage_acl_users", "")
        storage_acl_info_list = storage_acl_info.split(',')
        users_with_access = []
        for storage_acl_info_str in storage_acl_info_list:
            # try to identify user
            storage_acl_info_str = storage_acl_info_str.strip()
            user = (User.objects.filter(full_name__icontains=storage_acl_info_str.lower()) | User.objects.filter(
                full_name__icontains=storage_acl_info_str.upper())).first()
            if user is None:
                logger.warning('no user found for %s', storage_acl_info_str)
            else:
                users_with_access.append(user)
        return users_with_access

    def process_shares(self, dataset_dict, dataset):

        def process_share(share_object, dataset):
            share = Share()
            share.access_notes = share_object.get('share_notes')
            share.dataset = dataset
            share_institution_elu = share_object.get('share_inst')
            share_institution = Partner.objects.get(elu_accession=share_institution_elu.strip())
            share.partner = share_institution
            project = dataset.project
            if share_institution and project:
                contracts = project.contracts.all()
                for contract in contracts:
                    for partner in contract.partners:
                        if share_institution_elu.strip() == partner.elu_accession:
                            share.contract = contract
                            break
                if not share.contract:
                    contract = Contract.objects.create(
                        project=project,
                    )
                    contract.company_roles.add(GDPRRole["joint_controller"])
                    contract.add_partner_with_role(share_institution, GDPRRole["joint_controller"])
                    contract.local_custodians.set(project.local_custodians.all())
                    contract.save()
                    share.contract = contract
            return share

        shares = dataset_dict.get('shares', [])
        return [process_share(share_object, dataset) for share_object in shares]

    def process_category(self, storage_location_dict):
        category_str = storage_location_dict.get('category', '').strip().lower()
        try:
            return StorageLocationCategory[category_str]
        except KeyError:
            return StorageLocationCategory.not_specified

    def process_acl_info(self, storage_location_dict):
        if 'storage_acl_info' in storage_location_dict:

            return storage_location_dict['storage_acl_info']
        else:
            return None
