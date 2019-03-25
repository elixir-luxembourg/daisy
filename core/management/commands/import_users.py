from django.conf import settings
from django.core.management import BaseCommand

from ...importer.ldap_users_importer import LDAPUsersImporter


# TODO: really update rights of users. Disable users that are not in LDAP anymore, ...
class Command(BaseCommand):
    help = 'Import users from external system and update their rights.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip',
            action='store_true',
            dest='skip',
            help='Skip creation of users, only update their rights.'
        )

    def handle(self, *args, **options):
        class_filter = settings.LDAP_USERS_IMPORT_CLASS
        username_attribute = settings.LDAP_USERS_IMPORT_USERNAME_ATTR
        search_dn = settings.LDAP_USERS_IMPORT_SEARCH_DN
        ldap_users_importer = LDAPUsersImporter(class_filter, username_attribute, search_dn)
        skip = options.get('skip')
        if not skip:
            ldap_users_importer.import_all_users()
            pis = settings.PREDEFINED_PIS_LIST
            for pi in pis:
                try:
                    ldap_users_importer.import_from_username(pi, set_pi=True)
                except AttributeError:
                    pass
