from core.management.commands._private import ImportBaseCommand
from core.importer.datasets_importer import DatasetsImporter


class Command(ImportBaseCommand):
    help = 'Import datasets from JSON file(s)'

    def get_importer(
            self,
            publish_on_import=False,
            exit_on_error=False,
            verbose=False,
            validate=True,
            update=True
        ):
        return DatasetsImporter(publish_on_import, exit_on_error, verbose, validate, update)
