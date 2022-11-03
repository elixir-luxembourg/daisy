import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, ShareFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_share_add', 'dataset_share_remove', 'dataset_share_edit'])
def test_shares_views_permissions(permissions, group, url_name):
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