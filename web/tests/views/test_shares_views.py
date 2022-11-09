import pytest
from typing import Optional, Union
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, ShareFactory, UserFactory
from core.constants import Permissions
from core.models.user import User
from core.models.share import Share
from core.models.dataset import Dataset
from .utils import check_response_status


def check_share_views_permissions(url: str, user: User, action: Optional[Permissions], obj: Union[Share, Dataset], method: str):
    if isinstance(obj, Dataset):
        parent_dataset = obj
    else:
        parent_dataset = obj.dataset

    if action is not None:
        permission = f'core.{action.value}_dataset'
        if user.is_part_of(DataStewardGroup()):
            assert user.has_permission_on_object(permission, obj)
        else:
            assert not user.has_permission_on_object(permission, obj)

        check_response_status(url, user, [permission], obj, method)
        if user.is_part_of(VIPGroup()) and obj is not None:
            parent_dataset.local_custodians.set([user])
            assert user.has_permission_on_object(permission, obj)
            check_response_status(url, user, [permission], obj, method)

    else:
        check_response_status(url, user, [], obj, method)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, action',
    [
        ('dataset_share_add', Permissions.EDIT),
        ('dataset_share_remove', Permissions.EDIT),
        ('dataset_share_edit', Permissions.EDIT),
    ]
)
def test_shares_views_permissions(permissions, group, url_name, action):
    share = None
    dataset = DatasetFactory()
    dataset.save()

    kwargs = {'dataset_pk': dataset.pk}
    if url_name == 'dataset_share_remove':
        share = ShareFactory(dataset=dataset)
        share.save()
        kwargs.update({'share_pk': share.pk})

    elif url_name == 'dataset_share_edit':
        share = ShareFactory(dataset=dataset)
        share.save()
        kwargs.update({'pk': share.pk})

    url = reverse(url_name, kwargs=kwargs)
    assert url is not None
    user = UserFactory(groups=[group()])
    check_share_views_permissions(
        url,
        user,
        action,
        obj=share if share is not None else dataset,
        method="DELETE" if url_name == 'dataset_share_remove' else "GET")
