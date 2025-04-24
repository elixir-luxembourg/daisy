from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from core.models import Dataset, Project
from django.conf import settings
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = "Generate missing IDs for datasets and projects"

    def handle(self, *args, **options):
        self.stdout.write("Generating missing IDs...")

        with transaction.atomic():
            self.generate_ids(Dataset)
            self.generate_ids(Project)

        self.stdout.write(self.style.SUCCESS("ID generation complete!"))

    def generate_ids(self, model_class):
        entities = model_class.objects.filter(
            Q(elu_accession__isnull=True) | Q(elu_accession="")
        )
        self.stdout.write(
            f"Found {entities.count()} {model_class.__name__.lower()}s without IDs."
        )

        generate_id_function_path = getattr(settings, "IDSERVICE_FUNCTION", None)
        generate_id_function = None
        if generate_id_function_path:
            generate_id_function = import_string(generate_id_function_path)

        for entity in entities:
            try:
                if generate_id_function:
                    entity.elu_accession = generate_id_function(entity)
                    entity.save(update_fields=["elu_accession"])
                    self.stdout.write(
                        f"Generated ID: {entity.elu_accession} for {entity}"
                    )
            except Exception as e:
                self.stderr.write(f"Error generating ID for {entity}: {e}")
