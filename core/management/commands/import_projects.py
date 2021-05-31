from core.management.commands._private import ImportBaseCommand
from core.importer.projects_importer import ProjectsImporter


class Command(ImportBaseCommand):
    help = 'Import records from JSON file(s).'

    def get_importer(self):
        return ProjectsImporter()
