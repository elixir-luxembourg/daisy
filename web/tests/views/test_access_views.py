import pytest
from django.shortcuts import reverse

from core.constants import Permissions
from core.models.access import Access
from core.models.user import User
from core.models.dataset import Dataset
from test.factories import AccessFactory, DatasetFactory, VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, UserFactory

from .utils import check_response_status
from typing import Union


def check_access_view_permissions(url: str, user: User, obj: Union[Access, Dataset], method: str) -> None:
    # Any action on an Access instance needs the EDIT and PROTECTED permissions on parent dataset
    if isinstance(obj, Access):
        parent_dataset = obj.dataset
    else:
        parent_dataset = obj

    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)
    else:
        assert not user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)

    check_response_status(url, user, [f'core.{Permissions.EDIT.value}_dataset', f'core.{Permissions.PROTECTED.value}_dataset'], method=method, obj=obj)

    if user.is_part_of(VIPGroup()):
        user.save()
        parent_dataset.local_custodians.add(user)
        parent_dataset.save()
        assert user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)
        check_response_status(url, user, [f'core.{Permissions.EDIT.value}_dataset', f'core.{Permissions.PROTECTED.value}_dataset'], method=method, obj=obj)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_access_add', 'dataset_access_edit', 'dataset_access_remove'])
def test_access_views_permissions(permissions, users, group, url_name):
    """
    Tests whether users from different groups can create Access instances for a Dataset.

    Only data stewards and local custodians should be able to create Access instances.
    """
    dataset = DatasetFactory()
    access = None

    kwargs = {'dataset_pk': dataset.pk}
    if url_name != 'dataset_access_add':
        access = AccessFactory(dataset=dataset)
        access_key = 'pk' if url_name == 'dataset_access_edit' else 'access_pk'
        kwargs.update({access_key: access.pk})

    url = reverse(url_name, kwargs=kwargs)
    assert url is not None

    # Only users who can edit a dataset can create Access instances in it
    user = UserFactory(groups=[group()])

    obj = access if access is not None else dataset
    method = "DELETE" if url_name == "dataset_access_remove" else "GET"
    check_access_view_permissions(url, user, obj, method)
