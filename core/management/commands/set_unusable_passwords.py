from django.core.management import BaseCommand
from django.db import transaction

from core.models.user import User


class Command(BaseCommand):
    help = (
        "Set an unusable password for every user with an oidc_id. "
        "They authenticate with Keycloak, so their local password must not work anymore. "
        "A user without an oidc_id keeps it: the break-glass superuser, the demo accounts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without updating users",
        )

    def handle(self, *args, **options):
        # a superuser keeps the password to reach the admin when Keycloak is unavailable
        candidates = User.objects.filter(oidc_id__isnull=False, is_superuser=False)
        users = [user for user in candidates if user.has_usable_password()]

        prefix = "Would set" if options["dry_run"] else "Set"
        self.stdout.write(f"{prefix} an unusable password for {len(users)} user(s).")

        if options["dry_run"]:
            return

        with transaction.atomic():
            for user in users:
                user.set_unusable_password()
                user.save(update_fields=["password"])
