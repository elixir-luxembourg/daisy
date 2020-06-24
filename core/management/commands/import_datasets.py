import os

from django.core.management import BaseCommand, CommandError


from core.importer.datasets_importer import DatasetsImporter

JSON_SUFFIX = '.json'


class Command(BaseCommand):
    help = 'import datasets from folder containing JSON files'

    def add_arguments(self, parser):
        parser.add_argument('-d')
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
        )
        parser.add_argument(
            '--exit-on-error',
            action='store_true',
            dest='exit',
        )

    def handle(self, *args, **options):
        try:
            path_to_json_directory = options.get('d')
            verbose = options.get('verbose')
            exxit = options.get('exit')
            importer = DatasetsImporter()

            # We import all dataset files first
            for json_file_path in os.listdir(path_to_json_directory):
                if json_file_path.endswith(JSON_SUFFIX):
                    self.import_file(importer, os.path.join(path_to_json_directory, json_file_path), verbose,
                                     exxit)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR("Something went wrong during the import! Is the path valid? Is the file valid?"))
            self.stderr.write(self.style.ERROR(str(e)))

    def import_file(self, importer, full_path, verbose, exxit):
        with open(full_path) as json_file:
            json_file_contents = json_file.read()
            self.stdout.write("Importing file %s" % full_path)
            result = importer.import_json(json_file_contents, verbose=verbose)
            if result:
                self.stdout.write(self.style.SUCCESS("Import was successful!"))
            else:
                self.stdout.write(self.style.ERROR("Import failed"))
                if exxit:
                    raise CommandError('Exited after error.')
