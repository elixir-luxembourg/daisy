import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, DataLocationFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_storagelocation_add', 'dataset_storagelocation_remove', 'dataset_storagelocation_edit'])
def test_shares_views_permissions(permissions, group, url_name):
    dataset = DatasetFactory()
    dataset.save()

    kwargs = {'dataset_pk': dataset.pk}
    if url_name == 'dataset_storagelocation_remove':
        share = DataLocationFactory(dataset=dataset)
        share.save()
        kwargs.update({'storagelocation_pk': share.pk})

    elif url_name == 'dataset_storagelocation_edit':
        share = DataLocationFactory(dataset=dataset)
        share.save()
        kwargs.update({'pk': share.pk})

    url = reverse(url_name, kwargs=kwargs)
    assert url is not None