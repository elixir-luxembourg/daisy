from core.importer.base_importer import BaseImporter
from core.importer.JSONSchemaValidator import ProjectJSONSchemaValidator
from core.models import Partner, Project, Publication


class ProjectsImporter(BaseImporter):
    """
    `ProjectsImporter`, should be able to fill the database with projects' information, based on JSON file
    complying to the schema in:
     https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-project.json

    Usage example:
        def import_projects():
            importer = ProjectsImporter()
            importer.import_json_file("projects.json")
    """

    json_schema_validator = ProjectJSONSchemaValidator()
    json_schema_uri = 'https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-project.json'

    def process_json(self, project_dict):
        publications = [self.process_publication(publication_dict)
                        for publication_dict
                        in project_dict.get('publications', [])]

        name = project_dict.get('name', "N/A")
        if 'acronym' in project_dict:
            acronym = project_dict.get('acronym')
        else:
            acronym = name
        description = project_dict.get('description', None)
        elu_accession = project_dict.get('external_id', '-') or '-'
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
            acronym_to_show = acronym.encode('utf8')
            self.logger.warning(f"Project with acronym '{acronym_to_show}' already found. It will be updated.")
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
            date_str = project_dict.get('start_date')
            message = "\tCouldn't import the 'start_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + f'Was: "{date_str}". '
            message = message + "Continuing with empty value."
            self.logger.warning(message)

        try:
            if 'end_date' in project_dict and project_dict.get('end_date') and len(project_dict.get('end_date')) > 0:
                project.end_date = self.process_date(project_dict.get('end_date'))
        except self.DateImportException:
            date_str = project_dict.get('end_date')
            message = "\tCouldn't import the 'end_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + f'Was: "{date_str}". '
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

        return True

    @staticmethod
    def process_publication(publication_dict):
        # First, try to find if the publication is already in our database
        publication = None

        # Search by DOI
        if 'doi' in publication_dict and len(publication_dict.get('doi')) > 0:
            if Publication.objects.filter(doi=publication_dict.get('doi')).count() == 1:
                publication = Publication.objects.get(doi=publication_dict.get('doi'))
        
        # Search by citation string
        if publication is None and 'citation_string' in publication_dict and len(publication_dict.get('citation_string')) > 0:
            if Publication.objects.filter(citation=publication_dict.get('citation_string')).count() == 1:
                publication = Publication.objects.get(citation=publication_dict.get('citation_string'))

        # Create a new one if it does not exist
        if publication is None:
            publication = Publication.objects.create(citation=publication_dict.get('citation_string'))

        # Then proceed to filling the fields
        if 'doi' in publication_dict:
            publication.doi = publication_dict.get('doi')
        
        publication.save()
        return publication
