from collections import defaultdict

from django.core.management import BaseCommand, CommandError
from django.db import transaction
from guardian.conf import settings as guardian_settings

from core.lcsb.oidc import KeycloakBackend, get_keycloak_config_from_settings
from core.models.user import User


def normalized_email(email):
    return (email or "").strip().lower()


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
        accounts = backend.get_list_of_users()
        to_update, to_deactivate, unmatched = self.plan(
            accounts, options["deactivate_unmatched"]
        )

        self.stdout.write(
            f"{'Would update' if dry_run else 'Updated'} "
            f"{len(to_update)} user(s) with an oidc_id."
        )
        self.stdout.write(
            f"{'Would deactivate' if dry_run else 'Deactivated'} "
            f"{len(to_deactivate)} user(s)."
        )
        if not dry_run:
            self.apply(to_update, to_deactivate)
            return
        # these users cannot log in, a steward fixes the email or creates the account
        for user in unmatched:
            self.stdout.write(f"No Keycloak account: {user.email or user.username}")

    def plan(self, accounts, deactivate_unmatched):
        """
        Return the users to bind to a Keycloak account, the users to deactivate,
        and the active users that Keycloak does not know.
        """
        account_by_email = self.account_by_email(accounts)
        keycloak_ids = {account.id for account in accounts if account.id}

        # the guardian anonymous user is a system row, it has no Keycloak account
        users = list(
            User.objects.exclude(username=guardian_settings.ANONYMOUS_USER_NAME)
        )
        owner_by_oidc_id = {user.oidc_id: user for user in users if user.oidc_id}
        users_by_email = defaultdict(list)
        for user in users:
            users_by_email[normalized_email(user.email)].append(user)

        to_update = []
        to_deactivate = []
        unmatched = []
        for user in users:
            email = normalized_email(user.email)
            account = account_by_email.get(email)
            if user.oidc_id:
                found = user.oidc_id in keycloak_ids
            elif account:
                self.check_account_is_free(
                    account, users_by_email[email], owner_by_oidc_id
                )
                to_update.append((user, account.id))
                found = True
            else:
                found = False
            if found or not user.is_active:
                continue
            unmatched.append(user)
            # a superuser is the break-glass account, only a steward deactivates it
            if not user.is_superuser and (user.oidc_id or deactivate_unmatched):
                to_deactivate.append(user)
        return to_update, to_deactivate, unmatched

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
    def account_by_email(accounts):
        """
        Map every email to its single Keycloak account.
        A data steward has to resolve the emails with more than one account first.
        """
        accounts_by_email = defaultdict(list)
        for account in accounts:
            email = normalized_email(account.email)
            if email:
                accounts_by_email[email].append(account)

        shared_emails = {
            email: found for email, found in accounts_by_email.items() if len(found) > 1
        }
        if shared_emails:
            raise CommandError(
                "Multiple verified Keycloak accounts share an email; no changes made: "
                + "; ".join(
                    f"{email}: {', '.join(account.id for account in found)}"
                    for email, found in sorted(shared_emails.items())
                )
            )
        return {email: found[0] for email, found in accounts_by_email.items()}

    @staticmethod
    def check_account_is_free(account, users_with_that_email, owner_by_oidc_id):
        """
        Refuse to assign an oidc_id when the target is ambiguous or already taken.
        """
        if len(users_with_that_email) > 1:
            raise CommandError(
                f"Keycloak account {account.id} ({account.email}) matches multiple DAISY users "
                f"({', '.join(str(user.pk) for user in users_with_that_email)}); no changes made"
            )
        owner = owner_by_oidc_id.get(account.id)
        if owner:
            raise CommandError(
                f"Keycloak account {account.id} is already assigned to DAISY user {owner.pk}; "
                "no changes made"
            )
