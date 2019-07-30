import ldap
from django_auth_ldap.backend import LDAPBackend, _LDAPUser
from django_auth_ldap.config import LDAPSearch
from django.contrib.auth.models import Group
from core.importer.users_importer import UsersImporter
from core.constants import Groups as GroupConstants
from django.conf import settings


class LDAPUsersImporter(UsersImporter):

    def __init__(self, class_filter, username_attribute, search_dn, simple_search=True):
        self.search_dn = search_dn
        self.simple_search = simple_search
        self.username_attribute = username_attribute
        self.filter = class_filter

    # self.filter = settings.LDAP_USERS_IMPORT_CLASS
    # self.username_attribute = settings.LDAP_USERS_IMPORT_USERNAME_ATTR

    def import_all_users(self):
        ldap_backend = LDAPBackend()
        ldap_user = _LDAPUser(ldap_backend, username="")
        ldap_search = LDAPSearch(self.search_dn, ldap.SCOPE_SUBTREE,
                                 filterstr=self.filter,
                                 attrlist=[self.username_attribute])
        results = ldap_search.execute(connection=ldap_user.connection)
        for result in results:
            if self.simple_search:
                search_term = result[1][self.username_attribute][0]
            else:
                search_term = result[0].split(',')[0].split('=')[1]
            user = ldap_backend.populate_user(search_term)
            user.source = settings.USER_SOURCE['active_directory']
            user.save()

    def import_from_username(self, username, set_pi=False):
        ldap_backend = LDAPBackend()
        user = ldap_backend.populate_user(username)

        if set_pi:
            g = Group.objects.get(name=GroupConstants.VIP.value)
            user.groups.add(g)
            #user.save()
