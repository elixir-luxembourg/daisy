from core.management.commands._private import ImportBaseCommand
from core.importer.datasets_importer import DatasetsImporter


class Command(ImportBaseCommand):
    help = 'Import datasets from JSON file(s)'

    def get_importer(self):
        return DatasetsImporter()
