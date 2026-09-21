import pytest
from django.contrib.auth.models import Group
from django.conf import settings

from core.constants import Groups as GroupConstants
from core.importer.ldap_users_importer import LDAPUsersImporter
from core.models import User
from core.models.user import UserSource


def make_ldap_users_importer():
    class_filter = settings.LDAP_USERS_IMPORT_CLASS
    username_attribute = settings.LDAP_USERS_IMPORT_USERNAME_ATTR
    search_dn = settings.LDAP_USERS_IMPORT_SEARCH_DN
    assert class_filter
    assert username_attribute
    assert search_dn
    return LDAPUsersImporter(class_filter, username_attribute, search_dn, False)


@pytest.mark.django_db
def test_import_users():
    ldap_users_importer = make_ldap_users_importer()
    ldap_users_importer.import_all_users()
    assert 5 == User.objects.count()
    normal_user = User.objects.filter(username="normal.user").first()
    assert normal_user is not None
    assert "normal.user@uni.lu" == normal_user.email
    assert "Normal" == normal_user.first_name
    assert "User" == normal_user.last_name


@pytest.mark.django_db
def test_import_from_username_creates_inactive_user():
    user = make_ldap_users_importer().import_from_username("normal.user")

    assert user is not None
    assert user.username == "normal.user"
    assert user.email == "normal.user@uni.lu"
    assert user.source == UserSource.ACTIVE_DIRECTORY
    assert user.is_active is False


@pytest.mark.django_db
def test_import_from_username_returns_none_for_unknown_user():
    assert make_ldap_users_importer().import_from_username("missing.user") is None


@pytest.mark.django_db
def test_import_from_username_with_pi_creates_vip_group():
    user = make_ldap_users_importer().import_from_username("normal.user", set_pi=True)

    assert user is not None
    vip_group = Group.objects.get(name=GroupConstants.VIP.value)
    assert user.groups.filter(pk=vip_group.pk).exists()
