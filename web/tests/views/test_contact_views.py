import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ContactFactory

@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['contacts', 'contact_edit', 'contact_add', 'contact_delete', 'contacts_export'])
def test_contacts_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access the urls associated with Contact instances
    """
    if url_name in ['contacts', 'contact_add', 'contacts_export']:
        url = reverse(url_name)
    else:
        contact = ContactFactory()
        contact.save()
        url = reverse(url_name, kwargs={'pk': contact.pk})

    assert url is not None