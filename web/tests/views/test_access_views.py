import pytest

from test.factories import AccessFactory, DatasetFactory, VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, UserFactory
from django.shortcuts import reverse

from .utils import check_response_status


def check_access_view_permissions(url, user, parent_dataset):
    if user.is_part_of(DataStewardGroup):
        assert user.has_permission_on_object('core.edit_dataset', parent_dataset)
    else:
        assert not user.has_permission_on_object('core.edit_dataset', parent_dataset)

    check_response_status(url, user, 'core.edit_dataset', obj=parent_dataset)

    if user.is_part_of(VIPGroup):
        parent_dataset.local_custodians.add(user)
        parent_dataset.save()
        assert user.has_permission_on_object('core.edit_dataset', parent_dataset)
        check_response_status(url, user, 'core.edit_dataset', obj=parent_dataset)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_access_add', 'dataset_access_edit', 'dataset_access_remove'])
def test_access_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can create Access instances for a Dataset.

    Only data stewards and local custodians should be able to create Access instances.
    """
    dataset = DatasetFactory()

    kwargs = {'dataset_pk': dataset.pk}
    if url_name != 'dataset_access_add':
        access = AccessFactory(dataset=dataset)
        access_key = 'pk' if url_name == 'dataset_access_edit' else 'access_pk'
        kwargs.update({access_key: access.pk})

    url = reverse(url_name, kwargs=kwargs)
    assert url is not None

    # Only users who can edit a dataset can create Access instances in it
    user = UserFactory(groups=[group()])
    check_access_view_permissions(url, user, dataset)
