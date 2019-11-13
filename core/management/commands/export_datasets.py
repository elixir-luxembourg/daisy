import os

from django.core.management import BaseCommand

from core.importer.datasets_exporter import DatasetsExporter

JSON_SUFFIX = '.json'


class Command(BaseCommand):
    help = 'export dataset records to a designated file'

    def add_arguments(self, parser):
        parser.add_argument('-f')


    def handle(self, *args, **options):
        try:
            path_to_json_file = options.get('f')
            with open(path_to_json_file,  mode="w+", encoding='utf-8') as json_file:
                exp = DatasetsExporter()
                exp.export_to_file(json_file)
                self.stdout.write(self.style.SUCCESS("Export complete!"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR("Something went wrong during the export! Is the path valid? Is the file valid?"))
            self.stderr.write(self.style.ERROR(str(e)))