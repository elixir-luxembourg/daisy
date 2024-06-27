import pytest
from django.conf import settings

from core.importer.ldap_users_importer import LDAPUsersImporter
from core.models import User


@pytest.mark.django_db
def test_import_users():
    class_filter = settings.LDAP_USERS_IMPORT_CLASS
    username_attribute = settings.LDAP_USERS_IMPORT_USERNAME_ATTR
    search_dn = settings.LDAP_USERS_IMPORT_SEARCH_DN
    assert class_filter
    assert username_attribute
    assert search_dn
    ldap_users_importer = LDAPUsersImporter(
        class_filter, username_attribute, search_dn, False
    )
    ldap_users_importer.import_all_users()
    assert 5 == User.objects.count()
    normal_user = User.objects.filter(username="normal.user").first()
    assert normal_user is not None
    assert "normal.user@uni.lu" == normal_user.email
    assert "Normal" == normal_user.first_name
    assert "User" == normal_user.last_name
