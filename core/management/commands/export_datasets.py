from core.management.commands._private import ExportBaseCommand
from core.importer.datasets_exporter import DatasetsExporter


class Command(ExportBaseCommand):
    help = "export dataset records to a designated file"

    def get_exporter(self, include_unpublished=False):
        return DatasetsExporter(include_unpublished=include_unpublished)
