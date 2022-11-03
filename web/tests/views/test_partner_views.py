import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, PartnerFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['partners', 'partner_add', 'partners_export', 'partner', 'partner_delete', 'partner_edit', 'partner_publish', 'partner_unpublish'])
def test_partners_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access the urls associated with Partner instances
    """
    if url_name in ['partners', 'partner_add', 'partners_export']:
        url = reverse(url_name)
    else:
        partner = PartnerFactory()
        partner.save()
        url = reverse(url_name, kwargs={'pk': partner.pk})

    assert url is not None
