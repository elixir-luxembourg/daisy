from collections import defaultdict

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from core.lcsb.oidc import (
    KeycloakBackend,
    get_keycloak_config_from_settings,
)
from core.models.user import User


class Command(BaseCommand):
    help = "Reconcile DAISY users with verified Keycloak accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without updating users",
        )

    def handle(self, *args, **options):
        backend = KeycloakBackend(get_keycloak_config_from_settings())
        keycloak_users = backend.get_list_of_users()

        users_by_email = defaultdict(list)
        for keycloak_user in keycloak_users:
            email = (keycloak_user.email or "").strip().lower()
            if email:
                users_by_email[email].append(keycloak_user)

        ambiguous_emails = {
            email: accounts
            for email, accounts in users_by_email.items()
            if len(accounts) > 1
        }
        if ambiguous_emails:
            details = "; ".join(
                f"{email}: {', '.join(account.id for account in accounts)}"
                for email, accounts in sorted(ambiguous_emails.items())
            )
            raise CommandError(
                "Multiple verified Keycloak accounts share an email; no changes made: "
                + details
            )

        keycloak_by_email = {
            email: accounts[0] for email, accounts in users_by_email.items()
        }
        keycloak_ids = {account.id for account in keycloak_users if account.id}
        pending_updates = []
        pending_deactivations = []

        for user in User.objects.all():
            email = (user.email or "").strip().lower()
            account = keycloak_by_email.get(email)
            if user.oidc_id is None and account:
                pending_updates.append((user, account["id"]))
            if user.oidc_id and user.oidc_id not in keycloak_ids and user.is_active:
                pending_deactivations.append(user)

        prefix = "Would update" if options["dry_run"] else "Updated"
        self.stdout.write(f"{prefix} {len(pending_updates)} user(s) with an oidc_id.")
        prefix = "Would deactivate" if options["dry_run"] else "Deactivated"
        self.stdout.write(f"{prefix} {len(pending_deactivations)} user(s).")

        if options["dry_run"]:
            return

        with transaction.atomic():
            for user, oidc_id in pending_updates:
                user.oidc_id = oidc_id
                user.save(update_fields=["oidc_id"])
            for user in pending_deactivations:
                user.is_active = False
                user.save(update_fields=["is_active"])
