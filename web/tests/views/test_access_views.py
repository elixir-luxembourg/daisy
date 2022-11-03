import pytest

from django.shortcuts import reverse
from test.factories import AccessFactory, DatasetFactory, VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_access_add', 'dataset_access_remove', 'dataset_access_edit'])
def test_access_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can create/delete/update Access instances for a Dataset
    """
    dataset = DatasetFactory()
    dataset.save()

    if url_name == 'dataset_access_add':
        url = reverse(url_name, kwargs={'dataset_pk': dataset.pk}) is not None
    else:
        access = AccessFactory(dataset=dataset)
        access.save()

        # Someone decided to give different key names to access primary key for data_access_remove url
        if url_name == 'dataset_access_remove':
            access_key = 'access_pk'
        else:
            access_key = 'pk'

        url = reverse(url_name, kwargs={'dataset_pk': dataset.pk, access_key: access.pk}) is not None

    assert url is not None
