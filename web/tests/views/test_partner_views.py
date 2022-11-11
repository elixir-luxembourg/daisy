import pytest
from django.shortcuts import reverse
from typing import Optional

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, PartnerFactory, UserFactory
from core.models.user import User
from core.models.partner import Partner
from core.constants import Permissions
from .utils import check_response_status, check_datasteward_restricted_url


def check_partner_views_permissions(url: str, user: User, action: Optional[Permissions], partner: Optional[Partner]):
    if action is not None:
        if user.is_part_of(DataStewardGroup()):
            assert user.has_permission_on_object(f'core.{action.value}_partner', partner)
        else:
            assert not user.has_permission_on_object(f'core.{action.value}_partner', partner)
        check_response_status(url, user, [f'core.{action.value}_partner'], partner)

    else:
        check_response_status(url, user, [], partner)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, action',
    [
        ('partners', None),
        ('partner_add', None),
        ('partner', None),
        ('partner_delete', Permissions.DELETE),
        ('partner_edit', None),
    ]
)
def test_partners_views_permissions(permissions, group, url_name, action):
    """
    Tests whether users from different groups can access the urls associated with Partner instances
    """
    partner = None
    if url_name in ['partners', 'partner_add', 'partners_export']:
        url = reverse(url_name)
    else:
        partner = PartnerFactory()
        partner.save()
        url = reverse(url_name, kwargs={'pk': partner.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_partner_views_permissions(url, user, action, partner)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['partner_publish', 'partner_unpublish', 'partners_export'])
def test_partners_publications_and_export(permissions, group, url_name):
    user = UserFactory(groups=[group()])
    kwargs = {}
    if url_name != 'partners_export':
        partner = PartnerFactory()
        kwargs.update({'pk': partner.pk})
    url = reverse(url_name, kwargs=kwargs)
    check_datasteward_restricted_url(url, user)
