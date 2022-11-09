import pytest
from urllib.parse import urlparse
from django.shortcuts import reverse
from django.test.client import Client

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, UserFactory
from core.models.user import User
from elixir_daisy import settings

def check_user_views_permissions(url: str, user: User):
    client = Client()
    client.login(username=user.username, password=user.password)
    response = client.get(url)
    if user.is_superuser:
        assert response.status_code != 403
    else:
        assert response.status_code == 302
        url_components = urlparse(response.url)
        assert url_components.path.startswith(f'/{settings.LOGIN_URL}/')



@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, needs_superuser',
    [
        ('users', True),
        ('users_add', True),
        ('users_change_password', True),
        ('user', True),
        ('user_delete', True),
        ('user_edit', True),
    ]
)
def test_user_views_permissions(permissions, user_admin, group, url_name, needs_superuser):
    if url_name in ['users', 'users_add', 'users_change_password']:
        url = reverse(url_name)
    else:
        user_target = UserFactory()
        user_target.save()
        url = reverse(url_name, kwargs={'pk': user_target.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_user_views_permissions(url, user)
    check_user_views_permissions(url, user_admin)


