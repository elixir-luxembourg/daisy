import pytest

from typing import Dict, List

from core.models import User
from core.lcsb.oidc import KeycloakAccountSynchronizer, KeycloakSynchronizationMethod
from core.lcsb.rems import create_rems_entitlement
from test.factories import DatasetFactory, UserFactory


class KeycloakSynchronizationMethodMock(KeycloakSynchronizationMethod):
    def test_connection(self) -> bool:
        return True

    def get_list_of_users(self) -> List[Dict]:            
        if self.style == 1:
            users = []
        else:
            users = [{
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
        # TODO: this is not perfect; keycloak-admin should be mocked, and not the synchronizer
        return [
            {
                'id': user.get('id'), 
                'email': user.get('email'),
                'first_name': user.get('firstName', 'FIRST_NAME_MISSING'),
                'last_name': user.get('lastName', 'FIRST_NAME_MISSING'),
                'username': user.get('email')
            } for user in users if user.get('email', None) is not None
        ]

    @classmethod
    def create_for_empty_list(cls):
        obj = cls({}, False)
        obj.style = 1
        return obj

    @classmethod
    def create_for_filled_list(cls):
        obj = cls({}, False)
        obj.style = 0
        return obj


def test_keycloak_synchronization_config_validation():
    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({})
    
    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({}, False)
        kc._create_connection({})


def test_keycloak_synchronization():
    mock = KeycloakSynchronizationMethodMock.create_for_filled_list()
    synchronizer = KeycloakAccountSynchronizer(mock)

    current_external_accounts = mock.get_list_of_users()
    synchronizer.current_external_accounts = current_external_accounts
    accounts_to_be_created, accounts_to_be_patched = synchronizer.compare()

    assert len(accounts_to_be_created) == 2, "There should be 2 new accounts to be added" 
    assert len(accounts_to_be_patched) == 0, "There should be no accounts to be patched"
    
    user_count = User.objects.count()
    synchronizer._add_users(accounts_to_be_created)
    synchronizer._patch_users(accounts_to_be_patched)
    new_user_count = User.objects.count()

    assert user_count + 2 == new_user_count

def test_add_rems_entitlements():
    elu_accession='12345678'

    user = UserFactory(oidc_id='12345', email='example@example.org')
    user.save()

    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=elu_accession)
    dataset.save()

    create_rems_entitlement(user, 'Test Application', elu_accession, user.oidc_id, user.email)
    user.delete()
