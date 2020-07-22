from core.importer.base_importer import BaseImporter
from core.models import Partner, Project, Publication


class ProjectsImporter(BaseImporter):
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

    def process_json(self, project_dict):

        publications = [self.process_publication(publication_dict)
                        for publication_dict
                        in project_dict.get('publications', [])]

        title = project_dict.get('name', "N/A")
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
            self.logger.warning("Project with acronym '{}' already found. It will be updated.".format(acronym))
            project.title = title
            project.description = description
            project.has_cner = has_cner
            project.has_erp = has_erp
            project.cner_notes = cner_notes
            project.erp_notes = erp_notes

        try:
            if 'start_date' in project_dict and len(project_dict.get('start_date')) > 0:
                project.start_date = self.process_date(project_dict.get('start_date'))
        except BaseImporter.DateImportException:
            message = "\tCouldn't import the 'start_date'. Does it follow the '%Y-%m-%d' format?\n\t"
            message = message + 'Was: "{}". '.format(project_dict.get('start_date'))
            message = message + "Continuing with empty value."
            self.logger.warning(message)

        try:
            if 'end_date' in project_dict and len(project_dict.get('end_date')) > 0:
                project.end_date = self.process_date(project_dict.get('end_date'))
        except ProjectsImporter.DateImportException:
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

        publication = Publication.objects.create(citation=publication_dict.get('citation'))
        if 'doi' in publication_dict:
            publication.doi = publication_dict.get('doi')
            publication.save()


        return publication


