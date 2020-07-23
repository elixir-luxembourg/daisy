from core.management.commands._private import ExportBaseCommand

from core.importer.partners_exporter import PartnersExporter

JSON_SUFFIX = '.json'


class Command(ExportBaseCommand):
    help = 'Export partner records to a designated file'

    def get_exporter(self):
        return PartnersExporter()
