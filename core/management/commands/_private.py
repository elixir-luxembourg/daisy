import os

from django.core.management import BaseCommand, CommandError

JSON_SUFFIX = '.json'


class ImportBaseCommand(BaseCommand):
    help = 'Import records from JSON file(s)'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--directory',
            help='Directory with JSON files',
            default=False)
        parser.add_argument(
            '-f',
            '--file',
            help='Path to JSON file',
            default=False)
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
            verbose = options.get('verbose')
            exxit = options.get('exit')
            importer = self.get_importer()
            path_to_json_file = options.get('file')
            path_to_json_directory = options.get('directory')

            if not(path_to_json_directory or path_to_json_file):
                raise CommandError('Either directory or file must be specified!')

            # Import files from directory
            if path_to_json_directory:
                self.import_directory(importer, path_to_json_directory, verbose, exxit)

            # Import records from file
            if path_to_json_file:
                self.import_file(importer, path_to_json_file, verbose, exxit)

            self.stdout.write(self.style.SUCCESS("Import was successful!"))

        except Exception as e:
            msg = f"Something went wrong during the import ({__file__}:class {self.__class__.__name__})! Is the path valid? Is the file valid? Details:"
            self.stderr.write(
                self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))

    def get_importer(self):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")

    def import_directory(self, importer, dir_path, verbose, exxit):
        for json_file_path in os.listdir(dir_path):
            if json_file_path.endswith(JSON_SUFFIX):
                self.import_file(importer,json_file_path, verbose, exxit)

    def import_file(self, importer, full_path, verbose, exxit):
        with open(full_path) as json_file:
            json_file_contents = json_file.read()
            self.stdout.write("Importing file %s" % full_path)
            result = importer.import_json(json_file_contents, verbose=verbose)
            if not result:
                self.stdout.write(self.style.ERROR("Import failed"))
                if exxit:
                    raise CommandError('Exited after error.')


class ExportBaseCommand(BaseCommand):
    help = 'Export records to a designated JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            help='Path to JSON file',
            default=False)

    def handle(self, *args, **options):
        try:
            path_to_json_file = options.get('file')
            with open(path_to_json_file,  mode="w+", encoding='utf-8') as json_file:
                exp = self.get_exporter()
                exp.export_to_file(json_file)
                self.stdout.write(self.style.SUCCESS("Export complete!"))

        except Exception as e:
            msg = f"Something went wrong during the import ({__file__}:class {self.__class__.__name__})! Is the path valid? Is the file valid? Details:"
            self.stderr.write(
                self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))

    def get_exporter(self):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")
