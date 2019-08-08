import pytest
from django.urls import reverse

from django.contrib.auth.models import Group

from core import constants
from test import factories

@pytest.mark.parametrize('url_name,factory', [
    ('dataset_delete',factories.DatasetFactory)
])
def test_permissions_for_normal_user_on_delete_view(django_user_model, client, factory, url_name):
    obj = factory()
    url = reverse(url_name, args=[obj.pk])
    user = django_user_model.objects.create(username='test.user')
    user.set_password('pwd')
    user.save()
    client.login(username=user.username, password='pwd')
    response = client.post(url, follow=True)
    assert response.status_code == 403