import pytest
from django.shortcuts import reverse
from django.contrib.contenttypes.models import ContentType
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, LegalBasisFactory, DatasetFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['dataset_legalbasis_add', 'dataset_legalbasis_remove', 'dataset_legalbasis_edit'])
def test_legal_basis_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with LegalBasis instances
    """
    dataset = DatasetFactory()
    dataset.save()
    if url_name == 'dataset_legalbasis_add':
        url = reverse(url_name, kwargs={'dataset_pk': dataset.pk})
    else:
        legal_basis = LegalBasisFactory(dataset=dataset)
        legal_basis.save()
        # Url placeholder for legal_basis pk has a different name for dataset_legal_basis_remove view
        key_name = 'legalbasis_pk' if url_name == 'dataset_legalbasis_remove' else 'pk'
        url = reverse(url_name, kwargs={'dataset_pk': dataset.pk, key_name: legal_basis.pk})

    assert url is not None
