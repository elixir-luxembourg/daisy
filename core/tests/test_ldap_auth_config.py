import ldap
import pytest
from django.conf import settings
from django_auth_ldap.config import LDAPSearchUnion

pytestmark = pytest.mark.skipif(
    not getattr(settings, "LDAP_ENABLED", False),
    reason="LDAP not enabled",
)


def test_auth_ldap_user_search_is_union():
    assert isinstance(settings.AUTH_LDAP_USER_SEARCH, LDAPSearchUnion)


def test_auth_ldap_base_search():
    base = settings.AUTH_LDAP_USER_SEARCH.searches[0]
    assert base.base_dn and "OU=LCSB" in base.base_dn and "DC=uni" in base.base_dn
    assert base.scope == ldap.SCOPE_SUBTREE
    if base.filterstr:
        assert "userPrincipalName=%(user)s" in base.filterstr


def test_auth_ldap_allowed_user_searches_structure():
    searches = settings.AUTH_LDAP_USER_SEARCH.searches[1:]
    for s in searches:
        if s.base_dn:
            assert "OU=UNI-Users" in s.base_dn and "DC=uni" in s.base_dn
        assert s.scope == ldap.SCOPE_SUBTREE
        if s.filterstr:
            assert "userPrincipalName=%(user)s" in s.filterstr
            assert "objectClass=person" in s.filterstr


def test_auth_ldap_search_count():
    searches = settings.AUTH_LDAP_USER_SEARCH.searches
    ldap_filter = getattr(settings, "LDAP_USERS_FILTER", None)
    ldap_ext_filter = getattr(settings, "LDAP_EXT_USERS_FILTER", None)
    if not ldap_filter and not ldap_ext_filter:
        assert len(searches) == 1
    else:
        assert len(searches) > 1


@pytest.mark.django_db
def test_ldap_backend_in_authentication_backends():
    assert "django_auth_ldap.backend.LDAPBackend" in settings.AUTHENTICATION_BACKENDS
