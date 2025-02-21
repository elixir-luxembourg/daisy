from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from core.models import Dataset, Project
from core.lcsb.idservice import generate_identifier


class Command(BaseCommand):
    help = "Generate IDs for existing datasets and projects that lack accession numbers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--type",
            choices=["dataset", "project", "all"],
            default="all",
            help="Type of entities to process",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        entity_type = options["type"]

        if entity_type in ["dataset", "all"]:
            self.process_entities(Dataset, "datasets", dry_run)

        if entity_type in ["project", "all"]:
            self.process_entities(Project, "projects", dry_run)

    def process_entities(self, model_class, entity_type, dry_run):
        entities = model_class.objects.filter(
            Q(elu_accession__isnull=True) | Q(elu_accession="")
        )
        count = entities.count()

        self.stdout.write(f"Found {count} {entity_type} without IDs")

        if dry_run:
            return

        with transaction.atomic():
            for entity in entities:
                try:
                    entity.elu_accession = generate_identifier(entity)
                    entity.save(update_fields=["elu_accession"])
                    self.stdout.write(
                        f"Generated ID {entity.elu_accession} for {entity}"
                    )
                except Exception as e:
                    self.stderr.write(f"Failed to generate ID for {entity}: {str(e)}")
