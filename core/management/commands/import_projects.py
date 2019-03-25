from django.conf import settings
from django.core.management import BaseCommand

from core.importer.projects_importer import ProjectsImporter


class Command(BaseCommand):
    help = 'import projects from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('-f')

    def handle(self, *args, **options):
        try:
            path_to_json_file = options.get('f')
            with open(path_to_json_file) as json_file:
                json_file_contents = json_file.read()
                importer = ProjectsImporter()
                importer.import_json(json_file_contents)
                self.stdout.write(self.style.SUCCESS("Import was successful!"))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR("Something went wrong during the import! Is the path valid? Is the file valid?"))
            self.stderr.write(self.style.ERROR(str(e)))
