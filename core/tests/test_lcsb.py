import datetime

import pytest

from typing import Dict, List

from core.models import User
from core.models.access import StatusChoices
from core.lcsb.oidc import KeycloakAccountSynchronizer, KeycloakSynchronizationMethod
from core.lcsb.rems import create_rems_entitlement, extract_rems_data, build_default_expiration_date, \
    check_existence_automatic
from core.models.access import Access
from core.models.contact import Contact
from test.factories import ContactFactory, DatasetFactory, UserFactory, ExposureFactory, EndpointFactory, AccessFactory
from web.views.utils import get_user_or_contact_by_oidc_id


class KeycloakAdminConnectionMock:
    def well_know(self) -> bool:
        return True

    def get_users(self, query) -> List[Dict]:
        return [{
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "createdTimestamp": 1634231689999,
            "username": "0000-0001-2222-3333",
            "enabled": True,
            "totp": False,
            "emailVerified": True,
            "firstName": "TESTY",
            "lastName": "MCTesty",
            "email": "testy.mctesty@uni.lu",
            "disableableCredentialTypes": [],
            "requiredActions": [],
            "notBefore": 0,
            "access": {
                "manageGroupMembership": False,
                "view": True,
                "mapRoles": False,
                "impersonate": False,
                "manage": False
            }
        }, {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeef",
            "createdTimestamp": 1634231689998,
            "username": "0000-0001-2222-3334",
            "enabled": True,
            "totp": False,
            "emailVerified": True,
            "firstName": "BOBBY",
            "lastName": "FISCHER",
            "email": "bobby.fischer@gmail.com",
            "disableableCredentialTypes": [],
            "requiredActions": [],
            "notBefore": 0,
            "access": {
                "manageGroupMembership": False,
                "view": True,
                "mapRoles": False,
                "impersonate": False,
                "manage": False
            }
        }, {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeeg",
            "createdTimestamp": 1634231689997,
            "username": "0000-0001-2222-3335",
            "firstName": "Ann",
            "lastName": "Bann",
        }]


class KeycloakSynchronizationMethodMock(KeycloakSynchronizationMethod):
    def test_connection(self) -> bool:
        return True

    def __init__(self, config: Dict, connect=True) -> None:
        self.config = config
        self.keycloak_admin_connection = KeycloakAdminConnectionMock()

    @staticmethod
    def _validate_config(config: Dict) -> None:
        pass

    def get_keycloak_admin_connection(self) -> None:
        return KeycloakAdminConnectionMock()

    def _create_connection(self, config: Dict = None) -> KeycloakAdminConnectionMock:
        return KeycloakAdminConnectionMock()


def test_keycloak_synchronization_config_validation():
    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({})

    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({}, False)
        kc._create_connection({})


def test_extract_rems_data_empty_expiration():
    application_id = 4056
    resource_id = "TEST-2-5591E3-1"
    user_oidc_id = "4ce4f280-8095-4a20-bf19-6426d2292134"
    email = "john.doe@uni.lu"
    data = {"application": application_id, "resource": resource_id, "user": user_oidc_id,
            "mail": email, "end": None}
    application, resource, user_oidc_id, email, expiration_date = extract_rems_data(data)
    assert application == application_id
    assert resource == resource_id
    assert user_oidc_id == user_oidc_id
    assert email == email
    assert expiration_date == build_default_expiration_date()


def test_extract_rems_data_with_expiration():
    application_id = 4056
    resource_id = "TEST-2-5591E3-1"
    user_oidc_id = "4ce4f280-8095-4a20-bf19-6426d2292134"
    email = "john.doe@uni.lu"
    data = {"application": application_id, "resource": resource_id, "user": user_oidc_id,
            "mail": email, "end": "2023-08-03T23:59:59.000Z"}
    application, resource, user_oidc_id, email, expiration_date = extract_rems_data(data)
    assert application == application_id
    assert resource == resource_id
    assert user_oidc_id == user_oidc_id
    assert email == email
    assert expiration_date == datetime.date(2023, 8, 3)


def test_check_existence_automatic_positive():
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id='12345', email='example@example.org')
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    create_rems_entitlement(user, 'Test Application', resource_id, user.oidc_id, user.email, expiration_date)
    application_id = 4056
    email = "john.doe@uni.lu"
    data = {"application": application_id, "resource": resource_id, "user": user.oidc_id,
            "mail": email, "end": expiration_date.strftime('%Y-%m-%d') + "T23:59:59.000Z"}
    assert check_existence_automatic(data)


def test_check_existence_automatic_negative_mismatch():
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id='12345', email='example@example.org')
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    create_rems_entitlement(user, 'Test Application', resource_id, user.oidc_id, user.email, expiration_date)
    application_id = 4056
    email = "john.doe@uni.lu"
    # resource id is different
    data = {"application": application_id, "resource": "TEST-2-5591E3-2", "user": user.oidc_id,
            "mail": email, "end": expiration_date.strftime('%Y-%m-%d') + "T23:59:59.000Z"}
    assert not check_existence_automatic(data)
    # user id is different
    data = {"application": application_id, "resource": resource_id, "user": "xxx",
            "mail": email, "end": expiration_date.strftime('%Y-%m-%d') + "T23:59:59.000Z"}
    assert not check_existence_automatic(data)
    # expiration date is different
    data = {"application": application_id, "resource": resource_id, "user": user.oidc_id,
            "mail": email, "end": datetime.date.today().strftime('%Y-%m-%d') + "T23:59:59.000Z"}
    assert not check_existence_automatic(data)

def test_check_existence_automatic_negative_manually_created():
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    email = "john.doe@uni.lu"
    user = UserFactory(oidc_id='12345', email=email)
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    access = AccessFactory(dataset=dataset, user=user)
    access.grant_expires_on=expiration_date
    access.was_generated_automatically = False
    access.status = StatusChoices.active
    access.save()
    application_id = 4056
    data = {"application": application_id, "resource": resource_id, "user": user.oidc_id,
            "mail": email, "end": expiration_date.strftime('%Y-%m-%d') + "T23:59:59.000Z"}
    assert not check_existence_automatic(data)


def test_add_rems_entitlements():
    elu_accession = '12345678'
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)

    user = UserFactory(oidc_id='12345', email='example@example.org')
    user.save()

    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=elu_accession)
    dataset.save()

    create_rems_entitlement(user, 'Test Application', elu_accession, user.oidc_id, user.email, expiration_date)
    user.delete()


def test_permissions():
    user = UserFactory(oidc_id='12345')
    user.save()

    user2 = UserFactory(oidc_id='23456')
    user2.save()

    contact = ContactFactory()
    contact.save()

    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession='123')
    endpoint = EndpointFactory()
    _ = ExposureFactory(dataset=dataset, endpoint=endpoint)
    dataset.save()

    access = Access(access_notes='Access contact', contact=contact, dataset=dataset, status=StatusChoices.active)
    access.save()

    access2 = Access(access_notes='Access user', user=user, dataset=dataset, status=StatusChoices.active)
    access2.save()

    assert '123' in user.get_access_permissions()
    assert '123' in contact.get_access_permissions()
    assert len(user2.get_access_permissions()) == 0


def test_get_user_or_contact_by_oidc_id():
    user_found, contact_found, user, contact = get_user_or_contact_by_oidc_id('0')
    assert not user_found
    assert not contact_found

    user = UserFactory(oidc_id='123456')
    user.save()

    user_found, contact_found, user, contact = get_user_or_contact_by_oidc_id('123456')
    assert user_found
    assert not contact_found

    contact = ContactFactory(oidc_id='98765')
    contact.save()

    user_found, contact_found, user, contact = get_user_or_contact_by_oidc_id('98765')
    assert not user_found
    assert contact_found
