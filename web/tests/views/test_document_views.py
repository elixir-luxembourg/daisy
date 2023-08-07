import pytest
from typing import Optional, List
from django.shortcuts import reverse
from django.contrib.contenttypes.models import ContentType

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetDocumentFactory, ProjectDocumentFactory, ContractDocumentFactory, UserFactory
from core.constants import Permissions
from core.models.user import User
from core.models.document import Document
from core.models.contract import Contract
from .utils import check_response_status

def check_document_view_permissions(url: str, user: User, actions_list: List[Permissions], document: Optional[Document], method: str):
    """
    Checks that only data stewards and local custodians can edit documents from Dataset and Project instances.
    Users from LegalGroup can also edit documents from Contract instances
    """
    parent_object = document.content_object
    if user.is_part_of(DataStewardGroup()) \
            or (user.is_part_of(LegalGroup()) and isinstance(document.content_object, Contract)) \
            or (user.is_part_of(AuditorGroup()) and actions_list == [Permissions.PROTECTED]):
        assert all([user.has_permission_on_object(f'core.{action.value}_{parent_object.__class__.__name__.lower()}', document) for action in actions_list])

    else:
        assert not all([user.has_permission_on_object(f'core.{action.value}_{parent_object.__class__.__name__.lower()}', document) for action in actions_list])

    check_response_status(url, user, [f'core.{action.value}_{parent_object.__class__.__name__.lower()}' for action in actions_list], document, method)

    if user.is_part_of(VIPGroup()):
        document.content_object.local_custodians.set([user])
        assert all([user.has_permission_on_object([f'core.{action.value}_{parent_object.__class__.__name__.lower()}'], document) for action in actions_list])
        check_response_status(url, user, [f'core.{action.value}_{parent_object.__class__.__name__.lower()}' for action in actions_list], document, method)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('doc_factory', [DatasetDocumentFactory, ContractDocumentFactory, ProjectDocumentFactory])
@pytest.mark.parametrize(
    'url_name, actions',
    [
        ('document_add', [Permissions.EDIT]),
        ('document_delete', [Permissions.EDIT]),
        ('document_download', [Permissions.PROTECTED]),
        ('document_edit', [Permissions.EDIT, Permissions.PROTECTED]),

    ]
)
def test_document_views_permissions(permissions, group, doc_factory, url_name, actions):
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
    user = UserFactory(groups=[group()])
    check_document_view_permissions(url, user, actions, document, method="DELETE" if url_name == 'document_delete' else "GET")