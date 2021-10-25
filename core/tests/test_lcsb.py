from core.lcsb.rems import create_rems_entitlement
import pytest

from typing import Dict, List

from core.lcsb.oidc import KeycloakSynchronizationMethod
from test.factories import DatasetFactory, UserFactory

class KeycloakSynchronizationMethodMock(KeycloakSynchronizationMethod):
    def get_list_of_users(self) -> List[Dict]:
        def _item(a, b):
            return {'id': a, 'email': b}
            
        if self.style == 1:
            return []
        else:
            return [
                _item('5a812222-2222-2222-a111-a00009877654', 'john.dye@uni.lu'),
                _item('dddddddd-eeee-ffff-ffff-ba02d7654321', 'agatha.dye@uni.lu'),
            ]

    def return_empty_list(self):
        self.style = 1
        return self

    def return_filled_list(self):
        self.style = 2
        return self


def test_keycloak_synchronization_config_validation():
    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({})
    
    with pytest.raises(KeyError):
        kc = KeycloakSynchronizationMethod({}, False)
        kc._create_connection({})


def test_add_rems_entitlements():
    elu_accession='12345678'

    user = UserFactory(oidc_id='12345', email='example@example.org')
    user.save()

    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=elu_accession)
    dataset.save()

    create_rems_entitlement(user, 'Test Application', elu_accession, user.oidc_id, user.email)
    user.delete()
