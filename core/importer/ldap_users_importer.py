import ldap
from django.contrib.auth.models import Group
from django_auth_ldap.backend import LDAPBackend, _LDAPUser
from django_auth_ldap.config import LDAPSearch

from core.constants import Groups as GroupConstants
from core.importer.users_importer import UsersImporter
from core.models.user import User, UserSource


class LDAPUsersImporter(UsersImporter):
    def __init__(self, class_filter, username_attribute, search_dn, simple_search=True):
        self.search_dn = search_dn
        self.simple_search = simple_search
        self.username_attribute = username_attribute
        self.filter = class_filter

    # self.filter = settings.LDAP_USERS_IMPORT_CLASS
    # self.username_attribute = settings.LDAP_USERS_IMPORT_USERNAME_ATTR

    @staticmethod
    def _is_new_account(username):
        """
        Tell whether the import creates this account. get_or_build_user() matches the Django user
        on the username, case insensitive, so this repeats the same lookup before the import.
        """
        if isinstance(username, bytes):
            username = username.decode()
        return not User.objects.filter(username__iexact=username.lower()).exists()

    @staticmethod
    def _deactivate_new_account(user):
        """
        An imported account waits inactive: a user authenticates with Keycloak, and an inactive
        row keeps its api_key out of the API. A login never activates it, an administrator binds
        the Keycloak identity in the `oidc id` column of the user list.
        An account that exists keeps its is_active and its password: a re-import must not lock
        out a user that works today. populate_user() stores an unusable password for a new one.
        """
        user.is_active = False

    def import_all_users(self):
        ldap_backend = LDAPBackend()
        ldap_user = _LDAPUser(ldap_backend, username="")
        ldap_search = LDAPSearch(
            self.search_dn,
            ldap.SCOPE_SUBTREE,
            filterstr=self.filter,
            attrlist=[self.username_attribute],
        )
        results = ldap_search.execute(connection=ldap_user.connection)
        for result in results:
            if self.simple_search:
                search_term = result[1][self.username_attribute][0]
            else:
                search_term = result[0].split(",")[0].split("=")[1]
            django_username = ldap_backend.ldap_to_django_username(search_term)
            is_new = self._is_new_account(django_username)
            user = ldap_backend.populate_user(search_term)
            if user is None:
                continue
            user.source = UserSource.ACTIVE_DIRECTORY
            if is_new:
                self._deactivate_new_account(user)
            user.save()

    def import_from_username(self, username, set_pi=False):
        ldap_backend = LDAPBackend()
        django_username = ldap_backend.ldap_to_django_username(username)
        user = ldap_backend.populate_user(username)
        if user is None:
            return None

        user.source = UserSource.ACTIVE_DIRECTORY
        if self._is_new_account(django_username):
            self._deactivate_new_account(user)
        user.save()

        if set_pi:
            g, _ = Group.objects.get_or_create(name=GroupConstants.VIP.value)
            user.groups.add(g)

        return user
