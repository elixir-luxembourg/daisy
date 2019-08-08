import pytest
from django.urls import reverse

from django.contrib.auth.models import Group

from core import constants

@pytest.mark.xfail
@pytest.mark.parametrize('group,code', [
    (None, 403),
    (constants.Groups.VIP, 403),
    (constants.Groups.DATA_STEWARD, 200),
    (constants.Groups.AUDITOR, 403),
    (constants.Groups.LEGAL, 403),
])
def test_create_view(django_user_model, client, group, code):
    url = reverse('partner_add')
    user = django_user_model.objects.create(username='test.user')
    user.set_password('pwd')
    if group is not None:
        g, _ = Group.objects.get_or_create(name=group.value)
        user.groups.add(g)
    user.save()
    client.login(username=user.username, password='pwd')
    response = client.post(url, data={})
    assert response.status_code == code