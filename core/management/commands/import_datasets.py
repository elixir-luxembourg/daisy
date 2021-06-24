from core.management.commands._private import ImportBaseCommand
from core.importer.datasets_importer import DatasetsImporter


class Command(ImportBaseCommand):
    help = 'Import datasets from JSON file(s)'

    def get_importer(
            self,
            exit_on_error=False,
            verbose=False,
            validate=True):
        return DatasetsImporter(exit_on_error, verbose, validate)
