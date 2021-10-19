from core.management.commands._private import ExportBaseCommand

from core.importer.partners_exporter import PartnersExporter


class Command(ExportBaseCommand):
    help = 'Export partner records to a designated file'

    def get_exporter(
        self,
        include_unpublished=False
    
    ):
        return PartnersExporter(include_unpublished)
