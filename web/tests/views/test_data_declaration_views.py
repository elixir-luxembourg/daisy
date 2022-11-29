import pytest
from typing import Union
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, DataDeclarationFactory, UserFactory
from core.models.user import User
from core.models.dataset import Dataset
from core.models.data_declaration import DataDeclaration
from core.constants import Permissions
from .utils import check_response_status


def check_data_declaration_views_permissions(url: str, user: User, obj: Union[DataDeclaration, Dataset]):
    # User need EDIT permission on a dataset to modify DataDeclarations
    if isinstance(obj, Dataset):
        parent_dataset = obj
    else:
        parent_dataset = obj.dataset

    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)
        check_response_status(url, user, [f'core.{Permissions.EDIT.value}_dataset'], obj)
    else:
        assert not user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)
        if user.is_part_of(VIPGroup()):
            parent_dataset.local_custodians.set([user])
            assert user.has_permission_on_object(f'core.{Permissions.EDIT.value}_dataset', obj)
            check_response_status(url, user, [f'core.{Permissions.EDIT.value}_dataset'], obj)



@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name',
    [
        'data_declaration',
        'data_declarations_add',
        'data_declarations_duplicate',
        'data_declarations_delete',
        'data_declaration_edit',
        'data_declarations_add_sub_form',
        'data_declarations_get_contracts',
        'data_declarations_autocomplete',
        'data_dec_paginated_search',
    ]
)
def test_data_declarations_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with DataDeclaration instances
    """
    data_declaration = None
    dataset = DatasetFactory()
    dataset.save()

    kwargs = {}
    if url_name in ['data_declaration', 'data_declarations_duplicate', 'data_declarations_delete', 'data_declaration_edit']:
        data_declaration = DataDeclarationFactory(dataset=dataset)
        data_declaration.save()
        kwargs.update({'pk': data_declaration.pk})

    elif url_name == 'data_declarations_add':
        kwargs.update({'pk': dataset.pk})

    url = reverse(url_name, kwargs=kwargs)

    assert url is not None
    user = UserFactory(groups=[group()])
    obj = data_declaration if data_declaration is not None else dataset
    check_data_declaration_views_permissions(url, user, obj)
