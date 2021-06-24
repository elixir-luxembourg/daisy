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
            default=False
        )
        parser.add_argument(
            '-f',
            '--file',
            help='Path to JSON file',
            default=False
        )
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
        parser.add_argument(
            '--no-validation',
            action='store_false',
            help='JSON file(s) content is validated against JSON schema before import by default.',
            dest='skip_validation',
        )

    def handle(self, *args, **options):
        try:
            verbose = options.get('verbose')
            exit_on_error = options.get('exit')
            path_to_json_file = options.get('file')
            validate = not(options.get('no_validation'))
            path_to_json_directory = options.get('directory')

            importer = self.get_importer(
                exit_on_error, 
                verbose, 
                validate)

            if not(path_to_json_directory or path_to_json_file):
                raise CommandError('Either directory (--directory) or file (--file) argument must be specified!')

            # Import files from directory
            if path_to_json_directory:
                self.import_directory(importer, path_to_json_directory)

            # Import records from file
            if path_to_json_file:
                self.import_file(importer, path_to_json_file)

            self.stdout.write(self.style.SUCCESS("Import was successful!"))

        except Exception as e:
            msg = f"Something went wrong during the import ({__file__}:class {self.__class__.__name__})! Is the path valid? Is the file valid? Details:"
            self.stderr.write(
                self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))

    def get_importer(self):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")

    def import_directory(self, importer, dir_path):
        for json_file_path in os.listdir(dir_path):
            if json_file_path.endswith(JSON_SUFFIX):
                correct_path = os.path.join(dir_path, json_file_path)
                self.import_file(importer, correct_path)

    def import_file(self, importer, full_path):
        if importer.import_json_file(full_path):
            return
        self.stdout.write(self.style.ERROR("Import failed"))
        if importer.exit_on_error:
            raise CommandError('Exited after error.')


class ExportBaseCommand(BaseCommand):
    help = 'Export records to a designated JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            help='Path to JSON file',
            default=False
        )

    def handle(self, *args, **options):
        if not(options.get('file')):
            raise CommandError('File (--file) argument must be specified!')

        try:
            path_to_json_file = options.get('file')
            with open(path_to_json_file,  mode="w+", encoding='utf-8') as json_file:
                exp = self.get_exporter()
                exp.export_to_file(json_file)
                self.stdout.write(self.style.SUCCESS("Export complete!"))

        except Exception as e:
            msg = f"Something went wrong during the export ({__file__}:class {self.__class__.__name__})! Details:"
            self.stderr.write(
                self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))

    def get_exporter(self):
        raise NotImplementedError("Abstract method: Implement this method in the child class.")
