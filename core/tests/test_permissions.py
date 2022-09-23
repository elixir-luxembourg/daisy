import pytest

from core import constants
from core.permissions import ALL_PERMS, PERMISSION_MAPPING, AutoChecker
from test.factories import *


# test checker
@pytest.mark.parametrize('factory', [ContractFactory, DatasetFactory, ProjectFactory])
def test_should_have_no_permissions(permissions, factory):
    """
    A random user should not have any permissions
    """
    user = UserFactory()
    checker = AutoChecker(user)
    entity = factory()
    for should_not_have in ALL_PERMS:
        assert not checker.check(should_not_have, entity)


# test user
@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('klass_name', ['core.Project', ])
@pytest.mark.parametrize('attribute', ['project', 'dataset', 'contract'])
def test_object_global_permissions_for_admin_groups(group, klass_name, attribute, permissions):
    """
    Check if permissions are correctly set for user that belongs to a "admin" group
    """
    group = group()
    contract = ContractFactory()
    dataset = DatasetFactory()
    entities = {"project": contract.project, "contract": contract, "dataset": dataset}
    user = UserFactory.create(groups=[group])
    obj = entities.get(attribute)

    should_have_perms = set(PERMISSION_MAPPING.get(constants.Groups(group.name), {}).get(klass_name, []))
    should_not_have_perms = set(ALL_PERMS) - should_have_perms

    for perm in should_have_perms:
        assert user.has_permission_on_object(perm, obj)

    for perm in should_not_have_perms:
        assert not user.has_permission_on_object(perm, obj)


group_permissions_expectations = []  # tuples of ( group name, has PROTECTED permission)
for group_name, permission_mapping in PERMISSION_MAPPING.items():
    permissions = permission_mapping.get('core.Project', [])
    group_permissions_expectations.append(
        (group_name, constants.Permissions.PROTECTED in permissions)
    )


@pytest.mark.parametrize('Factory,attribute', [
    (DatasetDocumentFactory, 'dataset'),
    (ContractDocumentFactory, 'contract'),
])
@pytest.mark.parametrize('group,expected', group_permissions_expectations)
def test_global_document_perms(group, expected, Factory, attribute, permissions):
    """
    Test document objects for "admins".
    -> a document is viewable by anyone with the PROTECTED permission on the project.
    or the "admin" groups
    """
    group = Group.objects.get(name=group.value)
    contract = ContractFactory()
    dataset = DatasetFactory()
    entities = {"contract": contract, "dataset": dataset}
    document = Factory(content_object=entities.get(attribute))
    user = UserFactory.create(groups=[group])
    assert document.content_object
    assert expected == user.has_permission_on_object(constants.Permissions.PROTECTED, document)


@pytest.mark.parametrize('attribute', ['project', 'dataset', 'contract'])
@pytest.mark.parametrize('perm', [p for p in constants.Permissions])
def test_vip_membership_perms(perm, attribute, permissions):
    """
    A vip added has local custodian should have all permissions for all object in the membership.
    """
    group = Group.objects.get(name=constants.Groups.VIP.value)
    contract = ContractFactory()
    dataset = DatasetFactory.create(project=contract.project)
    entities = {"project": contract.project, "contract": contract, "dataset": dataset}
    user = UserFactory.create(groups=[group])
    user.assign_permissions_to_project(contract.project)
    assert user.has_permission_on_object(perm, entities.get(attribute))

# @pytest.mark.parametrize('attribute', ['project', 'dataset', 'contract'])
# @pytest.mark.parametrize('perm', [p for p in constants.Permissions])
# def test_not_vip_membership_perms(perm, attribute, permissions):
#     """
#     A vip added has local custodian should have all permissions for all object in the membership.
#     """
#     membership = None
#         #MembershipFactory()
#     user = UserFactory()
#     user.assign_permissions_to_project(membership.project)
#     if perm not in [constants.Permissions.ADMIN, constants.Permissions.PROTECTED]:
#         assert user.has_permission_on_object(perm, getattr(membership, attribute))
#     else:
#         assert not user.has_permission_on_object(perm, getattr(membership, attribute))


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('entity_factory', [AccessFactory, DataLocationFactory, LegalBasisFactory, ShareFactory, DatasetDocumentFactory])
def test_dataset_entity_permissions(group, entity_factory):
    user = UserFactory(groups=[group()])
    user.save()
    dataset = DatasetFactory(title="Test")
    dataset.save()

    new_entity = entity_factory(object_id=dataset.pk) \
        if entity_factory == DatasetDocumentFactory \
        else entity_factory(dataset=dataset)

    new_entity.save()

    if user.is_part_of(DataStewardGroup):
        assert user.has_permission_on_object(constants.Permissions.EDIT, new_entity)
    else:
        assert not user.has_permission_on_object(constants.Permissions.EDIT, new_entity)

        dataset.local_custodians.set([user])
        dataset.save()
        assert user.has_permission_on_object(constants.Permissions.EDIT, new_entity)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('entity_factory', [ProjectDocumentFactory])
def test_project_entity_permissions(group, entity_factory):
    user = UserFactory(groups=[group()])
    user.save()
    project = ProjectFactory(title="Test")
    project.save()

    new_entity = entity_factory(object_id=project.pk)
    new_entity.save()

    if user.is_part_of(DataStewardGroup):
        assert user.has_permission_on_object(constants.Permissions.EDIT, new_entity)
    else:
        assert not user.has_permission_on_object(constants.Permissions.EDIT, new_entity)

        project.local_custodians.set([user])
        project.save()
        assert user.has_permission_on_object(constants.Permissions.EDIT, new_entity)

