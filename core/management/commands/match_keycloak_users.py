"""
One-time match of the DAISY users with their Keycloak account, to run after the migration.
It writes an oidc_id when the match is unambiguous: one Keycloak account and one DAISY user for
the email. It reports every other case for a data steward, who binds the identity in the
`oidc id` column of the user list.
import_keycloak_users is the nightly job.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple

from django.core.management import BaseCommand
from django.db import transaction
from guardian.conf import settings as guardian_settings

from core.lcsb.oidc import (
    KeycloakBackend,
    accounts_by_email,
    get_keycloak_config_from_settings,
    provider_label,
)
from core.models.user import User
from core.synchronizers import OIDCUser
from core.utils import normalized_email


@dataclass
class MatchPlan:
    """Only to_bind changes the database, the other lists are the report."""

    to_bind: List[Tuple[User, OIDCUser]] = field(default_factory=list)
    no_account: List[User] = field(default_factory=list)
    several_accounts: List[Tuple[User, List[OIDCUser]]] = field(default_factory=list)
    several_users: List[Tuple[str, List[User]]] = field(default_factory=list)
    account_taken: List[Tuple[User, OIDCUser]] = field(default_factory=list)


class Command(BaseCommand):
    help = "Match the DAISY users with their Keycloak account by email, once after the migration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the matches without writing an oidc_id",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        backend = KeycloakBackend(get_keycloak_config_from_settings())
        plan = self.plan(backend.get_list_of_users())
        self.report(plan, dry_run)
        if not dry_run:
            self.apply(plan.to_bind)

    def plan(self, accounts: List[OIDCUser]) -> MatchPlan:
        """
        Decide per email, not per user: a user is bound only when nothing is ambiguous.
        """
        keycloak_account_by_email = accounts_by_email(accounts)
        taken_ids = set(
            User.objects.exclude(oidc_id=None).values_list("oidc_id", flat=True)
        )

        users_by_email = defaultdict(list)
        unbound_users = User.objects.filter(oidc_id__isnull=True).exclude(
            username=guardian_settings.ANONYMOUS_USER_NAME
        )
        for user in unbound_users:
            users_by_email[normalized_email(user.email)].append(user)

        plan = MatchPlan()
        for email, users in sorted(users_by_email.items()):
            candidates = keycloak_account_by_email.get(email, [])
            if not candidates:
                plan.no_account.extend(users)
            elif len(users) > 1:
                plan.several_users.append((email, users))
            elif len(candidates) > 1:
                plan.several_accounts.append((users[0], candidates))
            elif candidates[0].id in taken_ids:
                plan.account_taken.append((users[0], candidates[0]))
            else:
                plan.to_bind.append((users[0], candidates[0]))
        return plan

    def report(self, plan: MatchPlan, dry_run: bool) -> None:
        for user, candidates in plan.several_accounts:
            self.stdout.write(
                f"Several Keycloak accounts, not bound: {user.email} (DAISY user {user.pk})"
            )
            for account in candidates:
                self.stdout.write(f"  {account.id}  {provider_label(account)}")

        for email, users in plan.several_users:
            users_list = ", ".join(str(pk) for pk in sorted(user.pk for user in users))
            self.stdout.write(
                f"Several DAISY users, not bound: {email} (DAISY users {users_list})"
            )

        for user, account in plan.account_taken:
            self.stdout.write(
                f"Keycloak account {account.id} already belongs to another DAISY record, "
                f"not bound: {user.email} (DAISY user {user.pk})"
            )

        for user in plan.no_account:
            self.stdout.write(f"No Keycloak account: {user.email or user.username}")

        self.stdout.write(
            f"{'Would bind' if dry_run else 'Bound'} {len(plan.to_bind)} user(s) "
            f"to a Keycloak account."
        )

    @staticmethod
    def apply(to_bind: List[Tuple[User, OIDCUser]]) -> None:
        with transaction.atomic():
            for user, account in to_bind:
                user.oidc_id = account.id
                user.save(update_fields=["oidc_id"])
