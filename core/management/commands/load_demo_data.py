import os

from django.conf import settings
from django.core.management import BaseCommand

from core.importer.datasets_importer import DatasetsImporter
from core.importer.projects_importer import ProjectsImporter
from core.models import User


DEMO_DATA_DIR = os.path.join(settings.BASE_DIR, "data", "demo")


class Command(BaseCommand):
    help = "load demo data into the database"

    def _load_demo_projects(self):
        projects_json_file = os.path.join(DEMO_DATA_DIR, "projects.json")
        importer = ProjectsImporter(exit_on_error=False, verbose=True)
        importer.import_json_file(projects_json_file)
        self.stdout.write(self.style.SUCCESS("Project import successful!"))

    def _load_demo_datasets(self):
        dataset_json_file = os.path.join(DEMO_DATA_DIR, "datasets.json")
        importer = DatasetsImporter(exit_on_error=False, verbose=True)
        importer.import_json_file(dataset_json_file)
        self.stdout.write(self.style.SUCCESS("Dataset import successful!"))

    def _create_demo_superuser(self):
        if User.objects.filter(username="admin").count() == 0:
            admin_usr = User.objects.create_user(
                username="admin", password="", email="demo.admin@uni.lu"
            )
            admin_usr.is_superuser = True
            admin_usr.save()
            self.stdout.write(self.style.SUCCESS("Added the `admin` superuser!"))
        else:
            self.stdout.write(
                self.style.SUCCESS("The `admin` superuser already existed.")
            )

    def _reset_passwords(self):
        users = User.objects.all()
        for user in users:
            if not user.username == "AnonymousUser":
                user.is_active = True
                user.is_staff = True
                user.set_password("demo")
                user.save()
        self.stdout.write(
            self.style.SUCCESS("The passwords have been reset to `demo`!")
        )

    def handle(self, *args, **options):
        try:
            self._load_demo_projects()
            self._load_demo_datasets()
            self._create_demo_superuser()
            self._reset_passwords()

        except Exception as e:
            msg = f"""Something went wrong during loading demo data ({__file__}: class {self.__class__.__name__})!
Is the path valid? Are the files (/data/demo) valid? More details:
"""
            self.stderr.write(self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))
