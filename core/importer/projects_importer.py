from core.importer.base_importer import BaseImporter
from core.importer.JSONSchemaValidator import ProjectJSONSchemaValidator
from core.models import Partner, Project, Publication


class ProjectsImporter(BaseImporter):
    """
    `ProjectsImporter`, should be able to fill the database with projects' information, based on JSON file
    complying to the schema in:
     https://git-r3lab.uni.lu/pinar.alper/metadata-tools/blob/master/metadata_tools/resources/elu-project.json

    Usage example:
        def import_projects():
            with open("projects.json", "r") as file_with_projects:
                importer = ProjectsImporter()
                importer.import_json(file_with_projects.read())
    """

    json_schema_validator = ProjectJSONSchemaValidator()

    def process_json(self, project_dict):
        publications = [self.process_publication(publication_dict)
                        for publication_dict
                        in project_dict.get('publications', [])]

        acronym = project_dict.get('acronym')
        name = project_dict.get('name', "N/A")
        description = project_dict.get('description', None)
        elu_accession = project_dict.get('elu_accession', '-')
        has_cner = project_dict.get('has_national_ethics_approval', False)
        has_erp = project_dict.get('has_institutional_ethics_approval', False)
        cner_notes = project_dict.get('national_ethics_approval_notes', None)
        erp_notes = project_dict.get('institutional_ethics_approval_notes', None)

        project = Project.objects.filter(acronym=acronym).first()
        if project is None:
            project, _ = Project.objects.get_or_create(acronym=acronym,
                                                       title=name,
                                                       description=description,
                                                       has_cner=has_cner,
                                                       has_erp=has_erp,
                                                       cner_notes=cner_notes,
                                                       erp_notes=erp_notes,
                                                       elu_accession=elu_accession
            )
        else:
            self.logger.warning("Project with acronym '{}' already found. It will be updated.".format(acronym))
            project.title = name
            project.description = description
            project.has_cner = has_cner
            project.has_erp = has_erp
            project.cner_notes = cner_notes
            project.erp_notes = erp_notes
            project.elu_accession = elu_accession

        try:
            if 'start_date' in project_dict and project_dict.get('start_date') and len(project_dict.get('start_date')) > 0:
                project.start_date = self.process_date(project_dict.get('start_date'))
        except self.DateImportException:
            message = "\tCouldn't import the 'start_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + 'Was: "{}". '.format(project_dict.get('start_date'))
            message = message + "Continuing with empty value."
            self.logger.warning(message)

        try:
            if 'end_date' in project_dict and project_dict.get('end_date') and len(project_dict.get('end_date')) > 0:
                project.end_date = self.process_date(project_dict.get('end_date'))
        except self.DateImportException:
            message = "\tCouldn't import the 'end_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + 'Was: "{}". '.format(project_dict.get('end_date'))
            message = message + "Continuing with empty value."
            self.logger.warning(message)

        project.save()

        local_custodians, local_personnel, external_contacts = self.process_contacts(project_dict.get('contacts', []))

        if local_personnel:
            project.company_personnel.set(local_personnel, clear=True)

        if local_custodians:
            project.local_custodians.set(local_custodians, clear=True)

        if external_contacts:
            project.contacts.set(external_contacts, clear=True)

        for publication in publications:
            project.publications.add(publication)

        project.updated = True
        project.save()
        for local_custodian in local_custodians:
            local_custodian.assign_permissions_to_dataset(project)

    @staticmethod
    def process_publication(publication_dict):
        # First, try to find if the publication is already in our database
        publication = None

        # Search by DOI
        if 'doi' in publication_dict and len(publication_dict.get('doi')) > 0:
            publication = Publication.objects.filter(doi=publication_dict.get('doi'))
            if len(publication):
                publication = publication[0]
        
        # Search by citation string
        if publication is None and 'citation_string' in publication_dict and len(publication_dict.get('citation_string')) > 0:
            publication = Publication.objects.filter(citation=publication_dict.get('citation_string'))
            if len(publication):
                publication = publication[0]
            else:
                publication = None

        # Create a new one if it does not exist
        if publication is None:
            publication = Publication.objects.create(citation=publication_dict.get('citation_string'))

        # Then proceed to filling the fields
        if 'doi' in publication_dict:
            publication.doi = publication_dict.get('doi')
        
        publication.save()
        return publication
