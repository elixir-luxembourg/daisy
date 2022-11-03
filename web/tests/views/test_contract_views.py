import pytest
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ContractFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['contracts', 'contract_add', 'contracts_export', 'contract', 'add_partner_role_to_contract', 'contract_delete', 'contract_delete', 'contract_edit'])
def test_contract_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with Contract instances
    """
    if url_name in ['contracts', 'contract_add', 'contracts_export']:
        url = reverse(url_name)
    else:
        contract = ContractFactory()
        contract.save()
        url = reverse(url_name, kwargs={'pk': contract.pk})

    assert url is not None
