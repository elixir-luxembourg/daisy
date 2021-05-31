import os

import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.backends.postgresql.features import DatabaseFeatures
from guardian.shortcuts import assign_perm

from core.constants import Groups as GroupConstants
from core.management.commands.load_initial_data import Command as CommandLoadInitialData
from core.permissions import PERMISSION_MAPPING

FIXTURE_DIR = os.path.join(settings.BASE_DIR, 'core', 'fixtures')

## FAKE LDAP DIRECTORY
LCSB = ('OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux', {'ou': ['LCSB']})
disabled_lcsb = ('OU=LCSB,OU=Faculties,OU=UNI-DisabledUsers,DC=uni,DC=lux', {'ou': ['LCSB']})
administration = (
    'OU=Administration,OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux', {'ou': ['Administration']})


def make_fake_ldap_user(firstname, lastname, password='password', title='Test user', is_external=False):
    """
    Create a fake LDAP user
    """
    enc = lambda x: x.encode('utf-8')
    dn = 'LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux'
    if is_external:
        dn = 'Administration,OU=FSTC,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux'

    small = '%s.%s' % (firstname.lower(), lastname.lower())
    return (
        'CN=%s,OU=%s' % (small, dn),
        {
            'cn': [enc('%s.%s' % (firstname, lastname))],
            'userPassword': [password],
            'accountExpires': ["0".encode("utf-8")],
            'title': title,
            'userprincipalname': [enc('%s@uni.lux' % small)],
            'objectClass': 'person',
            'givenName': [enc(firstname)],
            'sn': [enc(lastname)],
            'displayName': [enc('%s %s' % (firstname, lastname))],
            'name': [enc('%s.%s' % (firstname, lastname))],
            'mail': [enc('%s@uni.lu' % small)],
            'manager': [
                'cn=Superman,OU=Administration,OU=FSTC,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux'.encode('utf-8')],
            'telephoneNumber': ['9999'.encode('utf-8')],
        }
    )


# This is the content of our mock LDAP directory. It takes the form
# {dn: {attr: [value, ...], ...}, ...}.
directory = dict([
    administration, LCSB, disabled_lcsb,
    make_fake_ldap_user('Normal', 'User'),
    make_fake_ldap_user('PI', 'number1'),
    make_fake_ldap_user('PI', 'number2'),
    make_fake_ldap_user('Data', 'Steward'),
    make_fake_ldap_user('External', 'User', is_external=True),
])


@pytest.fixture(autouse=True)
def configure_mock_ldap():
    from mockldap import MockLdap
    mockldap = MockLdap(directory)
    mockldap.start()
    yield
    mockldap.stop()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


# solr_process = solr_process(
#   executable=None,
#   host='solr',
#   port=8983,
#   core='daisy_test',
#   version='7.3',
#   timeout=60
# )
# daisy_test = solr_core('solr_process', 'daisy_test')
# solr = solr('daisy_test')

# @pytest.fixture(autouse=True)
# def enable_solr_access_for_all_tests(solr):
#     pass

@pytest.mark.transactional_db
@pytest.fixture(scope='function')
def celery_session_worker(celery_session_worker):
    yield celery_session_worker

# clients / users fixtures
# thoses users must correspond to those created in the LDAP tree
@pytest.fixture
def user_normal(django_user_model):
    u = django_user_model.objects.create(username='normal.user', password='password')
    u.save()
    return u


@pytest.fixture
def user_vip(django_user_model):
    u = django_user_model.objects.create(username='pi.number1', password='password')
    g, _ = Group.objects.get_or_create(name=GroupConstants.VIP.value)
    u.groups.add(g)
    return u


@pytest.fixture
def user_data_steward(django_user_model):
    u = django_user_model.objects.create(username='data.steward', password='password')
    g, _ = Group.objects.get_or_create(name=GroupConstants.DATA_STEWARD.value)
    u.groups.add(g)
    return u


@pytest.fixture
def users(django_user_model, user_normal, user_vip, user_data_steward):
    """
    Fixture that create users based on the ldap directory created.
    """
    password = 'password'

    u = django_user_model.objects.create(username='pi.number2', password=password)
    g, _ = Group.objects.get_or_create(name=GroupConstants.VIP.value)
    u.groups.add(g)
    u.save()

    u = django_user_model.objects.create(username='external.user', password=password)
    u.save()


@pytest.fixture
def permissions():
    """
    Create basic permission mapping
    """
    for group_enum, permission_mapping in PERMISSION_MAPPING.items():
        group, _ = Group.objects.get_or_create(name=group_enum.value)
        group.permissions.clear()
        for klassname, permissions in permission_mapping.items():
            model = apps.get_model(klassname)
            content_type = ContentType.objects.get_for_model(model)
            for perm in permissions:
                permission_object = Permission.objects.get(
                    content_type=content_type,
                    codename=perm.value,
                )
                assign_perm(permission_object, group)


@pytest.fixture
def contact_types():
    """
    Create storage resources
    """
    CommandLoadInitialData.create_contact_types()


@pytest.fixture
def gdpr_roles():
    CommandLoadInitialData.create_gdpr_roles()


@pytest.fixture
def storage_resources():
    """
    Create storage resources
    """
    CommandLoadInitialData.create_storage_resources()


@pytest.fixture
def data_types():
    """
    Create data types
    """
    CommandLoadInitialData.create_datatypes()


@pytest.fixture
def partners():
    """
    Create partners
    """
    CommandLoadInitialData.create_elu_institutions()


@pytest.fixture
def can_defer_constraint_checks():
    DatabaseFeatures.can_defer_constraint_checks = True
    yield
    DatabaseFeatures.can_defer_constraint_checks = False
