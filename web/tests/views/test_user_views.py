import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, UserFactory

@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['users', 'users_add', 'users_change_password', 'user', 'user_delete', 'user_edit'])
def test_user_views_permissions(permissions, group, url_name):
    if url_name in ['users', 'users_add', 'users_change_password']:
        url = reverse(url_name)
    else:
        user = UserFactory()
        user.save()
        url = reverse(url_name, kwargs={'pk': user.pk})

    assert url is not None