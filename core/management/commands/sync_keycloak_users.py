from collections import defaultdict
from typing import List, NamedTuple, Tuple

from django.core.management import BaseCommand, CommandError
from django.db import transaction
from guardian.conf import settings as guardian_settings

from core.lcsb.oidc import KeycloakBackend, get_keycloak_config_from_settings
from core.models.user import User
from core.synchronizers import OIDCUser


def normalized_email(email):
    return (email or "").strip().lower()


class SyncPlan(NamedTuple):
    to_update: List[Tuple[User, str]] = []  # user:oidc_id
    to_deactivate: List[User] = []
    no_kc_accounts: List[User] = []
    multiple_kc_accounts: List[Tuple[User, List[OIDCUser]]] = []


class Command(BaseCommand):
    help = "Reconcile DAISY users with verified Keycloak accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without updating users",
        )
        parser.add_argument(
            "--deactivate-unmatched",
            action="store_true",
            help="Also deactivate users without an oidc_id and without a Keycloak account",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        backend = KeycloakBackend(get_keycloak_config_from_settings())
        keycloak_accounts = backend.get_list_of_users()
        plan = self.plan(keycloak_accounts, options["deactivate_unmatched"])

        # report results via stdout
        for user, keycloak_candidates in plan.multiple_kc_accounts:
            self.stdout.write(
                f"Shared email, not bound: {user.email} (DAISY user {user.pk})"
            )
            for account in keycloak_candidates:
                provider = account.identity_provider or account.username
                self.stdout.write(f"  {account.id}  {provider}")

        for user in plan.no_kc_accounts:
            self.stdout.write(f"No Keycloak account: {user.email or user.username}.")

        self.stdout.write(
            f"{'Would update' if dry_run else 'Updated'} "
            f"{len(plan.to_update)} user(s) with an oidc_id."
        )
        self.stdout.write(
            f"{'Would deactivate' if dry_run else 'Deactivated'} "
            f"{len(plan.to_deactivate)} user(s)."
        )
        if not dry_run:
            self.apply(plan.to_update, plan.to_deactivate)
            return

    def plan(self, accounts, deactivate_unmatched) -> "SyncPlan":
        """
        Decide what to do with every DAISY user. A branch that handles the user stops there, the
        users that fall through are the ones that Keycloak does not know.
        """
        keycloak_accounts_by_email = self.keycloak_accounts_by_email(accounts)
        keycloak_account_ids = {account.id for account in accounts if account.id}
        daisy_users = list(
            User.objects.exclude(username=guardian_settings.ANONYMOUS_USER_NAME)
        )
        users_by_oidc_id = {user.oidc_id: user for user in daisy_users if user.oidc_id}

        users_by_email = defaultdict(list)
        for user in daisy_users:
            users_by_email[normalized_email(user.email)].append(user)

        sync_plan = SyncPlan()
        for user in daisy_users:
            email = normalized_email(user.email)
            keycloak_candidates = keycloak_accounts_by_email.get(email, [])
            if user.oidc_id:
                if user.oidc_id in keycloak_account_ids:
                    continue
            elif len(keycloak_candidates) > 1:
                sync_plan.multiple_kc_accounts.append((user, keycloak_candidates))
                continue
            elif keycloak_candidates:
                account = keycloak_candidates[0]
                self.check_account(account, users_by_email[email], users_by_oidc_id)
                sync_plan.to_update.append((user, account.id))
                continue

            sync_plan.no_kc_accounts.append(user)
            if self.must_deactivate(user, deactivate_unmatched):
                sync_plan.to_deactivate.append(user)
        return sync_plan

    @staticmethod
    def must_deactivate(user, deactivate_unmatched) -> bool:
        """A superuser is the break-glass account, only a steward deactivates it."""
        if not user.is_active or user.is_superuser:
            return False
        return bool(user.oidc_id) or deactivate_unmatched

    @staticmethod
    def apply(to_update, to_deactivate):
        with transaction.atomic():
            for user, oidc_id in to_update:
                user.oidc_id = oidc_id
                user.save(update_fields=["oidc_id"])
            for user in to_deactivate:
                user.is_active = False
                user.save(update_fields=["is_active"])

    @staticmethod
    def keycloak_accounts_by_email(accounts):
        """
        Group the Keycloak accounts by email. An account without an email is a system account.
        An email with more than one account is reported, it must not stop the other users.
        """
        grouped = defaultdict(list)
        for account in accounts:
            email = normalized_email(account.email)
            if email:
                grouped[email].append(account)
        return grouped

    @staticmethod
    def check_account(account, users_with_that_email, users_by_oidc_id):
        """
        Refuse to assign an oidc_id when the target is ambiguous or already taken.
        """
        if len(users_with_that_email) > 1:
            raise CommandError(
                f"Keycloak account {account.id} ({account.email}) matches multiple DAISY users "
                f"({', '.join(str(user.pk) for user in users_with_that_email)}); no changes made"
            )
        user = users_by_oidc_id.get(account.id)
        if user:
            raise CommandError(
                f"Keycloak account {account.id} is already assigned to DAISY user {user.pk}; "
                "no changes made"
            )
