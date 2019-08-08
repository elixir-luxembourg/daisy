import pytest
from django.urls import reverse

from django.apps import apps
from core import constants
from test import factories

@pytest.mark.parametrize('url_name,factory,model', [
    ('dataset_delete',factories.DatasetFactory, 'Dataset'),
    ('project_delete',factories.ProjectFactory, 'Project'),
])
def test_permissions_for_normal_user_on_delete_view(django_user_model, client, factory, url_name, model):
    obj = factory()
    url = reverse(url_name, args=[obj.pk])
    user = django_user_model.objects.create(username='test.user')
    user.set_password('pwd')
    user.save()
    client.login(username=user.username, password='pwd')
    response = client.get(url)
    assert response.status_code == 403
    response = client.post(url)
    assert response.status_code == 403
    Model = apps.get_model(app_label='core', model_name=model)
    assert Model.objects.filter(pk=obj.pk).exists()
