import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['datasets', 'datasets_export', 'dataset_add', 'dataset', 'dataset_delete', 'dataset_edit', 'dataset_publish', 'dataset_unpublish', 'data_declarations_add'])
def test_dataset_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with Dataset instances
    """
    if url_name in ['datasets', 'datasets_export', 'dataset_add']:
        url = reverse(url_name)
    else:
        dataset = DatasetFactory()
        dataset.save()
        url = reverse(url_name, kwargs={"pk": dataset.pk})

    assert url is not None