"""
Nightly job: create a DAISY user for every new Keycloak account, and update no stored row, so
that a job can never change a record that a data steward maintains.
No filter on the identity provider: one person with two accounts becomes two users.
match_keycloak_users is the one-time match of the migration.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from django.core.management import BaseCommand
from django.db import IntegrityError, transaction

from core.lcsb.oidc import KeycloakBackend, get_keycloak_config_from_settings
from core.models.contact import Contact
from core.models.user import User
from core.synchronizers import OIDCUser, create_user
from core.utils import normalized_email


@dataclass
class ImportPlan:
    """Only to_create changes the database, the other fields are the report."""

    to_create: List[OIDCUser] = field(default_factory=list)
    user_exists: List[Tuple[OIDCUser, int]] = field(default_factory=list)
    contacts: List[Tuple[OIDCUser, int]] = field(default_factory=list)
    disabled: List[OIDCUser] = field(default_factory=list)
    without_email: List[OIDCUser] = field(default_factory=list)


class Command(BaseCommand):
    help = "Create a DAISY user for every Keycloak account that DAISY does not know yet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the accounts to create without creating a user",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        backend = KeycloakBackend(get_keycloak_config_from_settings())
        plan = self.plan(backend.get_list_of_users())
        self.report(plan)
        created = [] if dry_run else self.apply(plan.to_create)
        self.report_created(plan, created, dry_run)

    def plan(self, keycloak_accounts: List[OIDCUser]) -> ImportPlan:
        """Sort the Keycloak accounts: the ones that fall through need a user."""
        daisy_user_ids = self.get_user_ids()
        contacts_oidc_ids = self.get_contacts_by_oidc_id()
        contacts_emails = self.get_records_by_email(Contact.objects.all())
        users_by_email = self.get_records_by_email(
            User.objects.filter(oidc_id__isnull=True, is_active=True)
        )

        plan = ImportPlan()
        for account in keycloak_accounts:
            email = normalized_email(account.email)
            if not email:
                plan.without_email.append(account)
                continue
            contact_pk = contacts_oidc_ids.get(account.id) or contacts_emails.get(email)
            if contact_pk:
                plan.contacts.append((account, contact_pk))
            if email in users_by_email:
                plan.user_exists.append((account, users_by_email[email]))

            if account.id in daisy_user_ids:
                continue
            if account.enabled is False:
                plan.disabled.append(account)
                continue
            plan.to_create.append(account)
        return plan

    @staticmethod
    def get_user_ids() -> set:
        return set(User.objects.exclude(oidc_id=None).values_list("oidc_id", flat=True))

    @staticmethod
    def get_contacts_by_oidc_id() -> dict:
        return dict(Contact.objects.exclude(oidc_id=None).values_list("oidc_id", "pk"))

    @staticmethod
    def get_records_by_email(queryset) -> dict:
        """The primary key per email. Two records with one email is a state to report, not to use."""
        records = {}
        for pk, email in queryset.values_list("pk", "email"):
            email = normalized_email(email)
            if email:
                records.setdefault(email, pk)
        return records

    def apply(self, to_create: List[OIDCUser]) -> List[User]:
        """
        One transaction per account: a row DAISY cannot create must not undo the night.
        Row by row, because bulk_create() would skip User.save().
        """
        created = []
        for account in to_create:
            try:
                with transaction.atomic():
                    created.append(create_user(account))
            except IntegrityError as exception:
                self.stdout.write(
                    f"Not created: {account.email} ({account.id}): {exception}"
                )
        return created

    def report(self, plan: ImportPlan) -> None:
        for account, user_pk in plan.user_exists:
            self.stdout.write(
                f"DAISY user {user_pk} has this email and no oidc_id, a second user: "
                f"{account.email} ({account.id})"
            )

        for account, contact_pk in plan.contacts:
            self.stdout.write(
                f"Contact {contact_pk} has this id or email, it needs a migration: "
                f"{account.email} ({account.id})"
            )

        if plan.disabled:
            self.stdout.write(
                f"Disabled in Keycloak, not created: {len(plan.disabled)} account(s)."
            )
        if plan.without_email:
            self.stdout.write(
                f"Without an email, not created: {len(plan.without_email)} account(s)."
            )

    def report_created(
        self, plan: ImportPlan, created: List[User], dry_run: bool
    ) -> None:
        if dry_run:
            self.stdout.write(f"Would create {len(plan.to_create)} user(s).")
            return
        self.stdout.write(f"Created {len(created)} user(s).")
