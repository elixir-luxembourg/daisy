import pytest
from typing import Optional
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ContractFactory, UserFactory
from core.constants import Permissions
from core.models.user import User
from core.models.contract import Contract

from .utils import check_response_status


def check_contract_view_permissions(url: str, user: User, action: Permissions, contract: Optional[Contract]):
    """
    Data stewards and Legal can edit/delete all contracts.
    Other users can edit/delete contracts if they are local custodians
    """
    if action:
        if user.is_part_of(DataStewardGroup()) or (user.is_part_of(LegalGroup()) and action != Permissions.DELETE):
            assert user.has_permission_on_object(f'core.{action.value}_contract', contract)
        else:
            assert not user.has_permission_on_object(f'core.{action.value}_contract', contract)

        check_response_status(url, user, [f'core.{action.value}_contract'], contract)
    else:
        check_response_status(url, user, [], contract)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, perm',
    [
        ('contracts', None),
        ('contract_add', None),
        # FIXME: Discuss this
        # 'contracts_export',
        ('contract', None),
        ('add_partner_role_to_contract', Permissions.EDIT),
        ('contract_delete', Permissions.DELETE),
        ('contract_edit', Permissions.EDIT),
    ]
)
def test_contract_views_permissions(permissions, group, url_name, perm):
    """
    Tests whether users from different groups can access urls associated with Contract instances
    """
    contract = None
    if url_name in ['contracts', 'contract_add', 'contracts_export']:
        url = reverse(url_name)
    else:
        contract = ContractFactory()
        contract.save()
        url = reverse(url_name, kwargs={'pk': contract.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_contract_view_permissions(url, user, perm, contract)


# FIXME
# @pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_contract_view_protected_documents(permissions):
    assert False