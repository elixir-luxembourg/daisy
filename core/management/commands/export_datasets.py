from core.management.commands._private import ExportBaseCommand
from core.importer.datasets_exporter import DatasetsExporter

JSON_SUFFIX = '.json'


class Command(ExportBaseCommand):
    help = 'export dataset records to a designated file'

    def get_exporter(self):
        return DatasetsExporter()
