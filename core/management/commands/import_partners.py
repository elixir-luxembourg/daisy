from core.management.commands._private import ImportBaseCommand
from core.importer.partners_importer import PartnersImporter


class Command(ImportBaseCommand):
    help = 'Import records from JSON file(s).'

    def get_importer(
            self,
            publish_on_import=False,
            exit_on_error=False,
            verbose=False,
            validate=True,
            update=True
        ):
        return PartnersImporter(publish_on_import, exit_on_error, verbose, validate, update)
