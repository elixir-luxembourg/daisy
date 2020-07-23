from core.management.commands._private import ExportBaseCommand
from core.importer.projects_exporter import ProjectsExporter

JSON_SUFFIX = '.json'


class Command(ExportBaseCommand):
    help = 'export project records to a designated file'

    def get_exporter(self):
        return ProjectsExporter()
