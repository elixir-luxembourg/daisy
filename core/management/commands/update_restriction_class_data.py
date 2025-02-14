import json
import os

from django.conf import settings
from django.core.management import BaseCommand
from core.models import RestrictionClass


FIXTURE_DIR = os.path.join(settings.BASE_DIR, "core", "fixtures")


class Command(BaseCommand):
    help = "update restriction class data"

    @staticmethod
    def update_data():
        with open(os.path.join(FIXTURE_DIR, "restriction-class.json"), "r") as handler:
            data = json.load(handler)
            for restriction_class in data:
                RestrictionClass.objects.update_or_create(**restriction_class)

    def handle(self, *args, **options):
        self.update_data()
        print("update complete")
