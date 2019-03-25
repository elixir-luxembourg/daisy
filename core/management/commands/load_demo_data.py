from django.core.management import BaseCommand
from django.conf import settings
import os

from core.importer.datadecs_importer import DatadecsImporter
from core.importer.datasets_importer import DatasetsImporter
from core.importer.projects_importer import ProjectsImporter
from core.models import User

DEMO_DATA_DIR = os.path.join(settings.BASE_DIR, 'data', 'demo')


class Command(BaseCommand):
    help = 'load demo data into the database'


    def handle(self, *args, **options):
        try:
            projects_json_file = os.path.join(DEMO_DATA_DIR, 'projects.json')
            with open(projects_json_file, encoding='utf-8') as json_file:
                json_file_contents = json_file.read()
                importer = ProjectsImporter()
                importer.import_json(json_file_contents)
                self.stdout.write(self.style.SUCCESS("Project import  successful!"))
            dataset_json_file = os.path.join(DEMO_DATA_DIR, 'datasets.json')
            with open(dataset_json_file, encoding='utf-8') as json_file:
                json_file_contents = json_file.read()
                importer = DatasetsImporter()
                importer.import_json(json_file_contents)
                self.stdout.write(self.style.SUCCESS("Dataset import  successful!"))
            datadecs_json = os.path.join(DEMO_DATA_DIR, 'datadecs.json')
            with open(datadecs_json, encoding='utf-8') as json_file:
                json_file_contents = json_file.read()
                importer = DatadecsImporter()
                importer.import_json(json_file_contents)
                self.stdout.write(self.style.SUCCESS("Data declaration import  successful!"))



            admin_usr = User.objects.create_user(username='admin', password='', email='demo.admin@uni.lu')
            admin_usr.is_superuser =True
            admin_usr.save()

            users = User.objects.all()
            for user in users:
                if not user.username == 'AnonymousUser':
                    user.is_active = True
                    user.is_staff = True
                    user.set_password('demo')
                    user.save()



        except Exception as e:
            self.stderr.write(
                self.style.ERROR("Something went wrong during the import! Is the path valid? Is the file valid?"))
            self.stderr.write(self.style.ERROR(str(e)))