import pytest
from django.shortcuts import reverse
from django.contrib.contenttypes.models import ContentType
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetDocumentFactory, ProjectDocumentFactory, ContractDocumentFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('doc_factory', [DatasetDocumentFactory, ContractDocumentFactory, ProjectDocumentFactory])
@pytest.mark.parametrize('url_name', ['document_add', 'document_delete', 'document_download', 'document_edit'])
def test_document_views_permissions(permissions, group, doc_factory, url_name):
    """
    Tests whether users from different group can access urls associated with Document instances
    """
    document = doc_factory()
    document.save()

    if url_name == 'document_add':
        content_type = ContentType.objects.get_for_model(document.content_object)
        url = reverse(url_name, kwargs={'object_id': document.content_object.id, 'content_type': content_type.pk})

    else:
        url = reverse(url_name, kwargs={"pk": document.pk})

    assert url is not None
