from django.conf import settings
from django.core.management import BaseCommand

from ...importer.ldap_users_importer import LDAPUsersImporter


class Command(BaseCommand):
    """
    Bulk import of the user definitions of an LDAP directory. Keycloak is the source of the
    accounts, and this command stays for the instances that still import from LDAP.
    It creates inactive and unbound accounts: an administrator binds the Keycloak identity in
    the `oidc id` column of /definitions/users, a first login creates a user of its own.
    """

    help = "Import the users of an LDAP directory."

    def handle(self, *args, **options):
        ldap_users_importer = LDAPUsersImporter(
            settings.LDAP_USERS_IMPORT_CLASS,
            settings.LDAP_USERS_IMPORT_USERNAME_ATTR,
            settings.LDAP_USERS_IMPORT_SEARCH_DN,
        )
        ldap_users_importer.import_all_users()
