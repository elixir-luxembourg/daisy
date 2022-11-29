import pytest
from typing import Union
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, DataLocationFactory, UserFactory
from core.constants import Permissions
from core.models.user import User
from core.models.dataset import Dataset
from core.models.storage_location import DataLocation
from .utils import check_response_status

def check_storage_location_views_permissions(url: str, user: User, action: Permissions, obj: Union[Dataset, DataLocation], method: str):
    if isinstance(obj, Dataset):
        parent_dataset = obj
    else:
        parent_dataset = obj.dataset

    permission = f'core.{action.value}_dataset'
    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(permission, obj)
    else:
        assert not user.has_permission_on_object(permission, obj)

    check_response_status(url, user, [permission], obj, method)

    if user.is_part_of(VIPGroup()):
        parent_dataset.local_custodians.set([user])
        assert user.has_permission_on_object(permission, obj)
        check_response_status(url, user, [permission], obj, method)



@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, action',
    [
        ('dataset_storagelocation_add', Permissions.EDIT),
        ('dataset_storagelocation_remove', Permissions.EDIT),
        ('dataset_storagelocation_edit', Permissions.EDIT),
    ]
)
def test_storage_locations_views_permissions(permissions, group, url_name, action):
    dataset = DatasetFactory()
    dataset.save()
    location = None

    kwargs = {'dataset_pk': dataset.pk}
    if url_name == 'dataset_storagelocation_remove':
        location = DataLocationFactory(dataset=dataset)
        location.save()
        kwargs.update({'storagelocation_pk': location.pk})

    elif url_name == 'dataset_storagelocation_edit':
        location = DataLocationFactory(dataset=dataset)
        location.save()
        kwargs.update({'pk': location.pk})

    url = reverse(url_name, kwargs=kwargs)
    assert url is not None
    user = UserFactory(groups=[group()])
    check_storage_location_views_permissions(
        url,
        user,
        action,
        location if location is not None else dataset,
        method="DELETE" if url_name == "dataset_storagelocation_remove" else "GET"
    )
