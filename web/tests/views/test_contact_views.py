import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ContactFactory, UserFactory

from .utils import check_response_status


def check_contact_view_permissions(url, user, contact):
    if contact is not None:
        assert user.has_permission_on_object('core.edit_contact', contact)

        if user.is_part_of(DataStewardGroup):
            assert user.has_permission_on_object('core.delete_contact', contact)
        else:
            assert not user.has_permission_on_object('core.delete_contact', contact)
    else:
        assert user.has_perm('core.add_contact')

    if url == 'contact_add':
        check_response_status(url, user, 'core.add_contact')

    elif url == 'contact_delete':
        check_response_status(url, user, 'core.delete_contact', obj=contact)

    elif url == 'contacts':
        check_response_status(url, user, 'core.view_contact')

    else:
        check_response_status(url, user, 'core.edit_contact', obj=contact)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['contacts', 'contact_edit', 'contact_add', 'contact_delete', 'contacts_export'])
def test_contacts_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access the urls associated with Contact instances
    """
    # For now, anyone can create or edit contacts, but only datastewards can delete
    # FIXME
    #   Discuss this!

    contact = None
    if url_name in ['contacts', 'contact_add', 'contacts_export']:
        url = reverse(url_name)
    else:
        contact = ContactFactory()
        contact.save()
        url = reverse(url_name, kwargs={'pk': contact.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_contact_view_permissions(url, user, contact)
