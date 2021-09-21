from core.management.commands._private import ExportBaseCommand
from core.importer.projects_exporter import ProjectsExporter


class Command(ExportBaseCommand):
    help = 'export project records to a designated file'

    def get_exporter(
            self,
            include_unpublished=False
        ):
        return ProjectsExporter(include_unpublished)
