import pytest
from django.shortcuts import reverse

from core.constants import Permissions
from test.factories import (
    DatasetFactory,
    ProjectFactory,
    UserFactory,
    VIPGroup,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
)
from .utils import check_response_status


def check_object_permissions_views(url, user, entity, entity_name):
    perm = f"core.{Permissions.ADMIN.value}_{entity_name}"
    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(perm, entity)
    else:
        assert not user.has_permission_on_object(perm, entity)

    check_response_status(url, user, [perm], entity)


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize(
    "factory, url_name",
    [(DatasetFactory, "permission_dataset"), (ProjectFactory, "permission_project")],
)
def test_object_permissions_views(permissions, group, factory, url_name):
    entity = factory()
    entity_name = entity.__class__.__name__.lower()

    url = reverse(url_name, kwargs={"pk": entity.pk})
    user = UserFactory(groups=[group()])

    check_object_permissions_views(url, user, entity, entity_name)
