from core.exceptions import DatasetImportError
from core.importer.base_importer import BaseImporter
from core.importer.JSONSchemaValidator import DatasetJSONSchemaValidator
from core.models import Access, Cohort, DataDeclaration, Dataset, DataType, Partner, \
    Project, StorageResource, Share, UseRestriction, PersonalDataType, LegalBasisType, LegalBasis
from core.models.data_declaration import ConsentStatus, DeidentificationMethod, \
    ShareCategory, SubjectCategory
from core.models.storage_location import StorageLocationCategory, DataLocation
from core.models.use_restriction import USE_RESTRICTION_CHOICES


class DatasetsImporter(BaseImporter):
    """
    `DatasetsImporter`, parse json representation of a set of datasets and store them in the database
    """

    json_schema_validator = DatasetJSONSchemaValidator()
    #json_schema_uri = 'https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-dataset.json'

    def process_json(self, dataset_dict):
        try:
            title = dataset_dict['name'].strip()
        except KeyError:
            raise DatasetImportError(data='dataset without title')

        def get_dataset(elu_accession, title):
            if elu_accession and elu_accession != '-':
                dataset = Dataset.objects.get(elu_accession=elu_accession)
            else: 
                dataset = Dataset.objects.get(title=title)
            return dataset
      
        try:
            dataset = get_dataset(elu_accession = dataset_dict.get('external_id', None), title=title)
            title_to_show = title.encode('utf8')
            if not self.update:
                self.logger.warning(f"Dataset with title '{title_to_show}' already found. The update will be skipped")
                return True
            self.logger.warning(f"Dataset with title '{title_to_show}' already found. It will be updated.")
            if dataset.is_published:
                raise DatasetImportError(data=f'Updating published entity is not supported - dataset: "{dataset.title}".')
        except Dataset.DoesNotExist:
            dataset = Dataset.objects.create(title=title)

        if 'project' in dataset_dict and dataset_dict['project']:
            dataset.project = self.process_project(dataset_dict['project'])

        dataset.sensitivity = dataset_dict.get('sensitivity', None)

        local_custodians, local_personnel, external_contacts = self.process_contacts(dataset_dict.get("contacts", []))

        if local_custodians:
            dataset.local_custodians.set(local_custodians, clear=True)

        data_locations = self.process_data_locations(dataset, dataset_dict)
        if data_locations:
            dataset.data_locations.set(data_locations, bulk=False)

        # users_with_access = self.process_user_acl(storage_location_dict)
        # if users_with_access:
        #     dl.users_with_access.set(users_with_access, bulk=False)
        # if 'storage_acl_notes' in storage_location_dict:
        #     dl.access_notes = storage_location_dict['storage_acl_notes']

        shares = self.process_transfers(dataset_dict, dataset)
        if shares:
            dataset.shares.set(shares, bulk=False)

        dataset.save()
        dataset.updated = True
        for local_custodian in local_custodians:
            local_custodian.assign_permissions_to_dataset(dataset)

        studies_map = self.process_datadeclarations(dataset_dict, dataset)

        # Must be run after processing data declarations
        self.process_studies(dataset_dict, studies_map)

        # Must be run after processing data declarations
        legal_bases = self.process_legal_bases(dataset_dict, dataset)
        if legal_bases:
            dataset.legal_basis_definitions.set(legal_bases, bulk=False)

        dataset.save()

        dataset.elu_accession = dataset_dict.get('elu_accession', '-') or '-'

        if self.publish_on_import:
            self.publish_object(dataset)

        return True

    # @staticmethod
    # def process_local_custodians(dataset_dict):
    #     result = []
    #
    #     local_custodians = dataset_dict.get('local_custodian', [])
    #
    #     for local_custodian in local_custodians:
    #         custodian_str_strip = local_custodian.strip()
    #         user = (User.objects.filter(full_name__icontains=custodian_str_strip.lower()) | User.objects.filter(
    #             full_name__icontains=custodian_str_strip.upper())).first()
    #         if user is None:
    #             names = custodian_str_strip.split(maxsplit=1)
    #
    #             if len(names) == 2:
    #                 logger.warning('no user found for %s and inactive user will be created', custodian_str_strip)
    #                 usr_name = names[0].strip().lower() + '.' + names[1].strip().lower()
    #                 user = User.objects.create(username=usr_name, password='', first_name=names[0], last_name=names[1],is_active=False,
    #                                            email='inactive.user@uni.lu',
    #                                            )
    #                 user.staff = True
    #                 g = Group.objects.get(name=GroupConstants.VIP.value)
    #                 user.groups.add(g)
    #                 user.save()
    #                 result.append(user)
    #
    #         else:
    #             result.append(user)
    #     return result

    def process_project(self, project_acronym):
        try:
            acronym = project_acronym.strip()
            project = Project.objects.get(acronym=acronym)
            return project
        except Project.DoesNotExist:
            msg = f"Tried to find project with acronym ='{acronym}'; it was not found. Will try to look for the acronym..."
            self.logger.warning(msg)

        try:
            project = Project.objects.get(title=acronym)
            return project
        except Project.DoesNotExist:
            msg = f"Tried to find project with title ='{acronym}'; it was not found. Will create a new one."
            self.logger.warning(msg)
            project = Project.objects.create(
                acronym=acronym,
                title=acronym
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
        if 'storages' in dataset_dict:

            for storage_location_dict in dataset_dict['storages']:
                backend_name = storage_location_dict['platform'].lower().strip()
                backend_name = backend_mapping.get(backend_name, backend_name)
                if not backend_name:
                    raise DatasetImportError(data=f'Not a proper backend name: "{backend_name}".')
                try:
                    backend = StorageResource.objects.get(slug=backend_name)
                except StorageResource.DoesNotExist:
                    raise DatasetImportError(data=f'Cannot find StorageResource with slug: "{backend_name}".')
                category = self.process_location_category(storage_location_dict)


                location_delimeted = '\n'.join(storage_location_dict['locations'])

                dl = DataLocation.objects.create(
                    category=category,
                    backend=backend,
                    dataset=dataset,
                    **{'location_description': location_delimeted}
                )
                master_locations = DataLocation.objects.filter(category=StorageLocationCategory.master, dataset=dataset)

                acl_policy_description = self.process_acl_info(storage_location_dict)
                if acl_policy_description:
                    acc = Access.objects.create(
                        dataset=dataset,
                        access_notes=acl_policy_description
                    )
                    acc.defined_on_locations.set(master_locations)
                    acc.save()
                data_locations.append(dl)
        return data_locations


    def process_transfers(self, dataset_dict, dataset):

        def process_transfer(share_dict, dataset):
            share = Share()
            share.share_notes = share_dict.get('transfer_details')
            share.dataset = dataset
            share.partner = self.process_partner(share_dict.get('partner'))
            share.granted_on = share_dict.get('transfer_date', None)
            # project = dataset.project
            # if share_institution and project:
            #     contracts = project.contracts.all()
            #     for contract in contracts:
            #         for partner in contract.partners:
            #             if share_institution_elu.strip() == partner.elu_accession:
            #                 share.contract = contract
            #                 break
            #     if not share.contract:
            #         contract = Contract.objects.create(
            #             project=project,
            #         )
            #         contract.company_roles.add(GDPRRole["joint_controller"])
            #         contract.add_partner_with_role(share_institution, GDPRRole["joint_controller"])
            #         contract.local_custodians.set(project.local_custodians.all())
            #         contract.save()
            #         share.contract = contract
            return share

        transfers = dataset_dict.get('transfers', [])
        return [process_transfer(transfer_dict, dataset) for transfer_dict in transfers]

    def process_location_category(self, storage_location_dict):
        category_str = storage_location_dict.get('category', '').strip().lower()
        try:
            return StorageLocationCategory[category_str]
        except KeyError:
            return StorageLocationCategory.not_specified

    def process_acl_info(self, storage_location_dict):
        if 'accesses' in storage_location_dict:
            return "\n".join(storage_location_dict['accesses'])
        else:
            return None

    def process_datadeclarations(self, dataset_dict, dataset):
        studies_map = {}
        datadec_dicts = dataset_dict.get('data_declarations', [])

        for ddec_dict in datadec_dicts:
            data_declaration, studies_map_key = self.process_datadeclaration(ddec_dict, dataset)
            studies_map[studies_map_key] = data_declaration

        return studies_map

    def process_datadeclaration(self, datadec_dict, dataset):
        try:
            title = datadec_dict['title']
            title_to_show = title.encode('utf-8')
        except KeyError:
            raise DatasetImportError(data='Data declaration title missing')

        try:
            datadec = DataDeclaration.objects.get(title=title.strip(), dataset=dataset)
        except DataDeclaration.DoesNotExist:
            datadec = None

        if datadec:
            msg = f"Data declaration with title '{title_to_show}' already found. It will be updated."
            self.logger.warning(msg)
        else:
            datadec = DataDeclaration.objects.create(title=title, dataset=dataset)

        if 'source_study' not in datadec_dict or len(datadec_dict.get('source_study')) == 0:
            self.logger.warning(f"Data declaration with title '{title_to_show}' has no `source_study` set - there will be a problem processing study/cohort data.")

        datadec.has_special_subjects = datadec_dict.get('has_special_subjects', False)
        datadec.data_types_notes = datadec_dict.get('data_type_notes', None)
        datadec.deidentification_method = self.process_deidentification_method(datadec_dict)
        datadec.subjects_category = self.process_subjects_category(datadec_dict)
        datadec.special_subjects_description = datadec_dict.get('special_subjects_description', None)
        datadec.other_external_id = datadec_dict.get('other_external_id', None)
        datadec.share_category = self.process_access_category(datadec_dict)
        datadec.access_procedure = datadec_dict.get('access_procedure', '')
        datadec.consent_status = self.process_constent_status(datadec_dict)
        datadec.comments = datadec_dict.get('source_notes', None)
        datadec.embargo_date = datadec_dict.get('embargo_date', None)
        datadec.storage_duration_criteria = datadec_dict.get("storage_duration_criteria", None)
        datadec.end_of_storage_duration = datadec_dict.get("storage_end_date", None)
        if 'data_types' in datadec_dict:
            datadec.data_types_received.set(self.process_datatypes(datadec_dict))

        # if 'contract_obj' not in kwargs:
        #     if 'source_collaboration' in datadec_dict:
        #         datadec.contract = self.process_source_contract(dataset, datadec_dict)
        # else:
        #     datadec.contract = kwargs.pop('contract_obj')
        # if datadec.contract:
        #     datadec.partner = datadec.contract.partners.first()
        self.process_use_restrictions(datadec, datadec_dict)
        datadec.dataset = dataset
        datadec.save()
        datadec.updated = True

        return datadec, datadec_dict.get('source_study')

    def process_datatypes(self, datadec_dict):
        datatypes = []
        for datatype_str in datadec_dict.get('data_types', []):
            datatype_str = datatype_str.strip()
            try:
                datatype, _ = DataType.objects.get_or_create(name=datatype_str)
            except DataType.DoesNotExist:
                self.logger.error('Import failed')
                raise DatasetImportError(data=f'Cannot find data type: "{datatype_str}".')
            datatypes.append(datatype)
        return datatypes

    def process_deidentification_method(self, datadec_dict):
        deidentification_method_str = datadec_dict.get('de_identification', '')
        try:
            return DeidentificationMethod[deidentification_method_str]
        except KeyError:
            return DeidentificationMethod.pseudonymization

    def process_subjects_category(self, datadec_dict):
        if 'subjects_category' in datadec_dict:
            sub_category_str = datadec_dict.get('subjects_category', '').strip()
            try:
                return SubjectCategory[sub_category_str]
            except KeyError:
                return SubjectCategory.unknown
        else:
            return SubjectCategory.unknown

    # def process_source_contract(self, dataset, datadec_dict):
    #
    #     contract_dict = datadec_dict['source_collaboration']
    #
    #     try:
    #         partner_elu = contract_dict['collab_inst']
    #         if partner_elu is None:
    #             raise DatasetImportError(f'Partner accession number is NULL!')
    #         partner = Partner.objects.get(elu_accession=partner_elu.strip())
    #     except KeyError:
    #         raise DatasetImportError(f'Contract partner accession number is missing')
    #     except Partner.DoesNotExist:
    #         raise DatasetImportError(f'Cannot find institution partner with the elu: {partner_elu}')
    #
    #     if 'collab_project' not in contract_dict:
    #         logger.debug(
    #             ' * Contract project missing! Skipping contract setting for datadeclaration : "{}"...'.format(
    #                 datadec_dict.get('title', 'N/A')))
    #         return None
    #     else:
    #         # create contract project if it does not exist
    #         try:
    #             project = Project.objects.get(acronym=contract_dict['collab_project'].strip())
    #         except Project.DoesNotExist:
    #             project = Project.objects.create(
    #                 acronym=contract_dict['collab_project'].strip()
    #             )
    #             project.local_custodians.set(dataset.local_custodians.all())
    #             project.save()
    #         try:
    #             contract = Contract.objects.get(
    #                 partners_roles__partner=partner,
    #                 project=project)
    #         except Contract.DoesNotExist:
    #             if 'collab_role' in contract_dict:
    #                 role_str = contract_dict['collab_role']
    #                 role = GDPRRole[role_str]
    #             else:
    #                 role = GDPRRole["joint_controller"]
    #
    #             contract = Contract.objects.create(
    #                 project=project,
    #             )
    #             contract.company_roles.add(role)
    #             contract.add_partner_with_role(partner=partner, role=role)
    #         contract.local_custodians.set(project.local_custodians.all())
    #
    #         if 'collab_pi' in contract_dict:
    #             contact_type_pi, _ = ContactType.objects.get_or_create(name="Principal_Investigator")
    #
    #             contract_pi_str = contract_dict['collab_pi']
    #             contract_split = contract_pi_str.split()
    #
    #             first_name = contract_split[0]
    #             last_name = " ".join(contract_split[1:])
    #             contact, _ = Contact.objects.get_or_create(
    #                 first_name=first_name,
    #                 last_name=last_name,
    #                 type=contact_type_pi
    #             )
    #             contact.partner = partner
    #             contact.save()
    #             partner_role = PartnerRole.objects.filter(contract=contract, partner=partner).first()
    #             partner_role.contacts.add(contact)
    #             partner_role.save()
    #
    #         contract.save()
    #         return contract

    def process_use_restrictions(self, data_dec, datadec_dict):
        use_restrictions = []
        for user_restriction_dict in datadec_dict['use_restrictions']:
            ga4gh_code = user_restriction_dict.get('use_class', '')
            notes = user_restriction_dict.get('use_restriction_note', '')
            use_class_note = user_restriction_dict.get('use_class_note', '')
            use_restriction_rule_str = user_restriction_dict.get('use_restriction_rule', '')
            try:
                use_restriction_rule = USE_RESTRICTION_CHOICES[use_restriction_rule_str]
            except KeyError:
                use_restriction_rule = '-'

            use_restriction, _ = UseRestriction.objects.get_or_create(
                data_declaration=data_dec,
                restriction_class=ga4gh_code,
                notes=notes,
                use_class_note=use_class_note,
                use_restriction_rule=use_restriction_rule
            )
            use_restrictions.append(use_restriction)
        return use_restrictions

    def process_access_category(self, datadec_dict):
        share_category_str = datadec_dict.get('access_category', '')
        if share_category_str:
            try:
                return ShareCategory[share_category_str]
            except KeyError:
                return None
        return None

    def process_constent_status(self, datadec_dict):
        if 'consent_status' not in datadec_dict:
            return ConsentStatus.unknown
        if datadec_dict['consent_status'] is None:
            return ConsentStatus.unknown
        consent_status_str = datadec_dict.get('consent_status', '').strip()
        try:
            return ConsentStatus[consent_status_str]
        except KeyError:
            return ConsentStatus.unknown
            
    def process_legal_bases(self, dataset_dict, dataset_object):
        """
        This should be called after data-declarations have been processed
        (they rely on data-declaration's acronyms to be properly imported)
        """
        if 'legal_bases' not in dataset_dict:
            return
        
        return [self.process_legal_basis(legal_basis, dataset_object) for legal_basis in dataset_dict.get('legal_bases')]

    def process_legal_basis(self, legal_basis, dataset_object):
        """
        This should be called after data-declarations have been processed
        (they rely on data-declaration's acronyms to be properly imported)
        """
        legal_basis_obj = LegalBasis.objects.filter(
            dataset=dataset_object,
            remarks=legal_basis.get('legal_basis_notes', '')
        )  # Note: at this point we can have 0, 1 or more LegalBasis objects

        data_declaration_titles = legal_basis.get('data_declarations', [])
        data_declarations = [DataDeclaration.objects.get(title=title, dataset=dataset_object) for title in data_declaration_titles]

        legal_basis_types_titles = legal_basis.get('legal_basis_codes', [])
        legal_basis_types = [LegalBasisType.objects.get(code=code) for code in legal_basis_types_titles]

        personal_data_types_titles = legal_basis.get('personal_data_codes', [])
        personal_data_types = [PersonalDataType.objects.get(code=code) for code in personal_data_types_titles]

        if len(legal_basis_obj) == 0:
            legal_basis_obj = LegalBasis.objects.create(
                dataset=dataset_object,
                remarks=legal_basis.get('legal_basis_notes', '')
            )
        elif len(legal_basis_obj) == 1:
            legal_basis_obj = legal_basis_obj[0]
        else:
            # Try looking for the correct LegalBasis
            legal_basis_obj = LegalBasis.objects.filter(
                dataset=dataset_object,
                remarks=legal_basis.get('legal_basis_notes', ''),
                data_declarations__in=data_declarations
            )

            if len(legal_basis_obj) == 1:
                legal_basis_obj = legal_basis_obj[0]
            else:
                legal_basis_obj = LegalBasis.objects.create(
                    dataset=dataset_object,
                    remarks=legal_basis.get('legal_basis_notes', '')
                )

        legal_basis_obj.data_declarations.set(data_declarations)
        legal_basis_obj.legal_basis_types.set(legal_basis_types)
        legal_basis_obj.personal_data_types.set(personal_data_types)
        legal_basis_obj.save()

        return legal_basis_obj

    def process_studies(self, dataset_dict, studies_map):
        def _process_study(study):
            name = study.get('name', '')
            safe_name = name.encode('utf-8')
            description = study.get('description', '')
            has_ethics_approval = study.get('has_ethics_approval', False)
            ethics_approval_notes = study.get('ethics_approval_notes', '')
            url = study.get('url', '')

            try:
                cohort = Cohort.objects.get(title=name)
            except Cohort.DoesNotExist:
                cohort = None
            
            if cohort:
                msg = f"Cohort with title '{safe_name}' already found. All fields are going to be updated."
                self.logger.warning(msg)
            else:
                cohort = Cohort.objects.create(title=name)

            cohort.description = description
            cohort.ethics_confirmation = has_ethics_approval
            cohort.ethics_notes = ethics_approval_notes
            cohort.cohort_web_page = url
            cohort.save()
            cohort.updated = True
            
            local_custodians, local_personnel, external_contacts = self.process_contacts(study.get("contacts", []))
            cohort.owners.set(external_contacts)

            cohort.save()
            cohort.updated = True
            msg = f"Cohort '{safe_name}' imported successfully. Will try to link it to the data declaration..."
            self.logger.info(msg)

            try:
                data_declaration = studies_map.get(name)
                if data_declaration is None:
                    raise KeyError()
                if not isinstance(data_declaration, DataDeclaration):
                    raise KeyError()
                data_declaration.cohorts.add(cohort)
                data_declaration.save()
                safe_title = data_declaration.title.encode('utf8')
                self.logger.info(f"Cohort '{safe_name}' linked successfully to data declaration '{safe_title}'")
            except:
                self.logger.warning(f"The data declaration for the study '{safe_name}' not found. ")

        if 'studies' not in dataset_dict:
            return

        for study in dataset_dict.get('studies'):
            _process_study(study)
