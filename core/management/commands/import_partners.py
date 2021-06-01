from core.management.commands._private import ImportBaseCommand
from core.importer.partners_importer import PartnersImporter


class Command(ImportBaseCommand):
    help = 'Import records from JSON file(s).'

    def get_importer(self):
        return PartnersImporter()
