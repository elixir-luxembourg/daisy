import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, PublicationFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['publications', 'publication_add', 'publication_edit'])
def test_publication_views_permissions(permissions, group, url_name):
    if url_name == 'publication_edit':
        publication = PublicationFactory()
        publication.save()

        url = reverse(url_name, kwargs={"pk": publication.pk})

    else:
        url = reverse(url_name)

    assert url is not None