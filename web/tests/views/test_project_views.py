import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, ProjectFactory, ContactFactory, ContractFactory, UserFactory, PublicationFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name',
    [
        'projects',
        'projects_export',
        'project_add',
        'project',
        'project_delete',
        'project_edit',
        'project_publish',
        'project_unpublish',
        'add_contact_to_project',
        'datasets_add_to_project',
        'add_personnel_to_project',
        'add_publication_to_project',
        'remove_contact_from_project',
        'remove_personnel_from_project',
        'remove_publication_from_project',
        'pick_contact_for_project',
        'pick_publication_for_project',
        'project_contract_create',
        'project_contract_remove',
        'project_dataset_add',
        'project_dataset_choose_type',
        # 'project_dataset_create',  # FIXME: Actually never used anywhere in the code?
    ]
)
def test_project_views_permissions(permissions, group, url_name):
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


# FIXME
# @pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
def test_project_view_protected_documents(permissions):
    assert False