import pytest
from typing import Optional
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ProjectFactory, ContactFactory, ContractFactory, UserFactory, PublicationFactory
from core.models.user import User
from core.models.project import Project
from core.constants import Permissions
from .utils import check_response_status


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
        ('projects_export', None),
        ('project_add', None),
        ('project', None),
        ('project_delete', Permissions.DELETE),
        ('project_edit', Permissions.EDIT),
        # FIXME: Needs discussion
        # 'project_publish',
        # 'project_unpublish',
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
        # 'project_dataset_create',  # FIXME: Actually never used anywhere in the code?
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

# FIXME
# @pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_project_view_protected_documents(permissions):
    assert False