import os
import pytest
from typing import Optional
from django.shortcuts import reverse
from django.test.client import Client

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ProjectFactory, ContactFactory, ContractFactory, UserFactory, PublicationFactory, ProjectDocumentFactory
from core.models.user import User
from core.models.project import Project
from core.constants import Permissions
from .utils import check_response_status, check_datasteward_restricted_url, check_response_context_data


def check_project_views_permissions(url: str, user: User, action: Optional[Permissions], project: Optional[Project], method: str):

    if action is not None:
        permission = f'core.{action.value}_project'
        if user.is_part_of(DataStewardGroup()):
            assert user.has_permission_on_object(permission, project)
        else:
            assert not user.has_permission_on_object(permission, project)
        check_response_status(url, user, [permission], project, method)

        if user.is_part_of(VIPGroup()) and project is not None:
            project.local_custodians.set([user])
            assert user.has_permission_on_object(permission, project)
            check_response_status(url, user, [permission], project, method)

    else:
        check_response_status(url, user, [], project, method)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, action',
    [
        ('projects', None),
        ('project_add', None),
        ('project', None),
        ('project_delete', Permissions.DELETE),
        ('project_edit', Permissions.EDIT),
        ('add_contact_to_project', Permissions.EDIT),
        ('datasets_add_to_project', None),
        ('add_personnel_to_project', Permissions.EDIT),
        ('add_publication_to_project', Permissions.EDIT),
        ('remove_contact_from_project', Permissions.EDIT),
        ('remove_personnel_from_project', Permissions.EDIT),
        ('remove_publication_from_project', Permissions.EDIT),
        ('pick_contact_for_project', Permissions.EDIT),
        ('pick_publication_for_project', Permissions.EDIT),
        ('project_contract_create', Permissions.EDIT),
        ('project_contract_remove', Permissions.EDIT),
        ('project_dataset_add', Permissions.EDIT),
        ('project_dataset_choose_type', Permissions.EDIT),
    ]
)
def test_project_views_permissions(permissions, group, url_name, action):
    project = None
    if url_name in ['projects', 'projects_export', 'project_add']:
        url = reverse(url_name)
    else:
        project = ProjectFactory()
        project.save()
        kwargs = {'pk': project.pk}
        if url_name == 'remove_contact_from_project':
            contact = ContactFactory()
            contact.save()
            kwargs.update({'contact_id': contact.pk})

        elif url_name == 'remove_personnel_from_project':
            user = UserFactory()
            user.save()
            kwargs.update({'user_id': user.pk})

        elif url_name == 'remove_publication_from_project':
            publication = PublicationFactory()
            publication.save()
            kwargs.update({'publication_id': publication.pk})

        elif url_name == 'project_contract_remove':
            contract = ContractFactory(project=project)
            contract.save()
            kwargs.update({'cid': contract.pk})

        url = reverse(url_name, kwargs=kwargs)

    assert url is not None
    user = UserFactory(groups=[group()])
    if url_name in ['remove_contact_from_project', 'remove_personnel_from_project', 'remove_publication_from_project']:
        method = "DELETE"
    else:
        method = "GET"

    check_project_views_permissions(url, user, action, project, method)

@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_project_view_protected_documents(permissions, group):
    project = ProjectFactory()
    user = UserFactory(groups=[group()])

    client = Client()
    assert client.login(username=user.username, password='test-user'), "Login failed"

    url = reverse('project', kwargs={"pk": project.pk})
    response = client.get(url, follow=True)

    if user.is_part_of(DataStewardGroup(), AuditorGroup()):
        assert b'<div class="row mt-4" id="documents-card">' in response.content
        assert b'<h2 class="card-title"><span><i class="material-icons">link</i></span> Documents</h2>' in response.content
    else:
        assert b'<div class="row mt-4" id="documents-card">' not in response.content
        assert b'<h2 class="card-title"><span><i class="material-icons">link</i></span> Documents</h2>' not in response.content

    if user.is_part_of(VIPGroup()):
        project.local_custodians.set([user])
        response = client.get(url, follow=True)
        assert b'<div class="row mt-4" id="documents-card">' in response.content
        assert b'<h2 class="card-title"><span><i class="material-icons">link</i></span> Documents</h2>' in response.content


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_project_edit_protected_documents(permissions, group):
    document = ProjectDocumentFactory.create(with_file=True)
    project = document.content_object
    user = UserFactory(groups=[group()])

    client = Client()
    assert client.login(username=user.username, password='test-user'), "Login failed"

    url = reverse('project', kwargs={"pk": project.pk})
    response = client.get(url, follow=True)

    if user.is_part_of(DataStewardGroup()):
        assert b'<div class="ml-1 float-right btn-group" id="add-project-document">' in response.content
        assert b'<th id="document-action-head" style="width:7em">Actions</th>' in response.content
        assert b'<td id="document-action">' in response.content

    else:
        assert b'<div class="ml-1 float-right btn-group" id="add-project-document">' not in response.content
        assert b'<th id="document-action-head" style="width:7em">Actions</th>' not in response.content
        assert b'<td id="document-action">' not in response.content

    if user.is_part_of(VIPGroup()):
        project.local_custodians.set([user])
        response = client.get(url, follow=True)
        assert b'<div class="ml-1 float-right btn-group" id="add-project-document">' in response.content
        assert b'<th id="document-action-head" style="width:7em">Actions</th>' in response.content
        assert b'<td id="document-action">' in response.content

    os.remove(document.content.name)

@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['projects_export'])
def test_projects_publications_and_export(permissions, group, url_name):
    user = UserFactory(groups=[group()])
    kwargs = {}
    if url_name != 'projects_export':
        project = ProjectFactory()
        kwargs.update({'pk': project.pk})
    url = reverse(url_name, kwargs=kwargs)
    check_datasteward_restricted_url(url, user)


@pytest.mark.parametrize('context_key, permission_key', [
    ('can_edit', f'core.{Permissions.EDIT.value}_project'),
    ('is_admin', f'core.{Permissions.ADMIN.value}_project')
])
@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_project_views_context(permissions, context_key, permission_key, group):
    user = UserFactory(groups=[group()])
    project = ProjectFactory()

    url = reverse('project', kwargs={'pk': project.pk})
    check_response_context_data(url, user, permission_key, project, context_key)
