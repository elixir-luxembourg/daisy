import pytest

from typing import Dict, List

from core.lcsb.oidc import KeycloakSynchronization

class KeycloakSynchronizationMock(KeycloakSynchronization):
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
        kc = KeycloakSynchronization({})
    
    with pytest.raises(KeyError):
        kc = KeycloakSynchronization({}, False)
        kc._create_connection({})

