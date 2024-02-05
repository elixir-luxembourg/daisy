import pytest

from django.contrib.auth.models import Group

from core import constants
from core.permissions import GROUP_PERMISSIONS
from test.factories import (
    ContractFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
    AccessFactory,
    DataLocationFactory,
    LegalBasisFactory,
    ShareFactory,
    DatasetDocumentFactory,
    ProjectDocumentFactory,
    ContractDocumentFactory,
    VIPGroup,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
)


# test checker
@pytest.mark.parametrize("factory", [ContractFactory, DatasetFactory, ProjectFactory])
@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
def test_entity_default_permissions(permissions, factory, group):
    """
    Tests whether a user from a given group has the correct permissions on different Entities

    FIXTURES:
        permissions: Fixture to initialize permissions of users

    PARAMETERS:
        factory: An entity factory to create a contract, dataset, or project
        group: The group the user belongs to
    """
    user = UserFactory(groups=[group()])
    user.save()
    entity = factory()
    entity.save()

    if user.is_part_of(VIPGroup()):
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        entity.local_custodians.set([user])
        entity.save()
        # assert user.has_permission_on_object(constants.Permissions.VIEW, entity)
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )

    elif user.is_part_of(AuditorGroup()):
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )

    elif user.is_part_of(LegalGroup()) and factory == ContractFactory:
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )

        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )

    elif user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )

    else:
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.ADMIN.value}_{entity.__class__.__name__.lower()}",
            entity,
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_{entity.__class__.__name__.lower()}",
            entity,
        )


# test user
@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize(
    "klass_name",
    [
        "core.Project",
    ],
)
@pytest.mark.parametrize("attribute", ["project", "dataset", "contract"])
@pytest.mark.skip
def test_object_global_permissions_for_admin_groups(
    group, klass_name, attribute, permissions
):
    """
    Check if permissions are correctly set for user that belongs to a "admin" group
    """
    group = group()
    contract = ContractFactory()
    dataset = DatasetFactory()
    entities = {"project": contract.project, "contract": contract, "dataset": dataset}
    user = UserFactory.create(groups=[group])
    obj = entities.get(attribute)

    should_have_perms = set(
        GROUP_PERMISSIONS.get(constants.Groups(group.name), {}).get(klass_name, [])
    )
    should_not_have_perms = (
        set([perm.value for perm in constants.Permissions]) - should_have_perms
    )

    for perm in should_have_perms:
        assert user.has_permission_on_object(perm, obj)

    for perm in should_not_have_perms:
        assert not user.has_permission_on_object(perm, obj)


group_permissions_expectations = []  # tuples of ( group name, has PROTECTED permission)
for group_name, permission_mapping in GROUP_PERMISSIONS.items():
    group_permissions_expectations.append(
        (
            group_name,
            {
                model.split(".")[1]
                .lower(): model.replace(
                    ".", f".{constants.Permissions.PROTECTED.value}_"
                )
                .lower()
                in permissions
                for model, permissions in permission_mapping.items()
            },
        )
    )


@pytest.mark.parametrize(
    "Factory,attribute",
    [
        (DatasetDocumentFactory, "dataset"),
        (ProjectDocumentFactory, "project"),
        (ContractDocumentFactory, "contract"),
    ],
)
@pytest.mark.parametrize("group,expected", group_permissions_expectations)
def test_global_document_perms(group, expected, Factory, attribute, permissions):
    """
    Test document objects for "admins".
    -> a document is viewable by anyone with the PROTECTED permission on the project.
    or the "admin" groups
    """
    group = Group.objects.get(name=group.value)
    contract = ContractFactory()
    dataset = DatasetFactory()
    project = ProjectFactory()
    entities = {"contract": contract, "project": project, "dataset": dataset}
    document = Factory(content_object=entities.get(attribute))
    user = UserFactory.create(groups=[group])
    assert document.content_object
    assert expected.get(attribute, False) == user.has_permission_on_object(
        f"core.{constants.Permissions.PROTECTED.value}_{attribute}", document
    )


@pytest.mark.parametrize("attribute", ["project", "dataset", "contract"])
@pytest.mark.parametrize("perm", [p for p in constants.Permissions])
@pytest.mark.skip("VIP Group does not exist anymore for permissions")
def test_vip_membership_perms(perm, attribute, permissions):
    """
    A user added as local custodian should have all permissions for all objects in the membership.
    """
    group = Group.objects.get(name=constants.Groups.VIP.value)
    contract = ContractFactory()
    dataset = DatasetFactory.create(project=contract.project)
    entities = {"project": contract.project, "contract": contract, "dataset": dataset}
    user = UserFactory.create(groups=[group])
    user.assign_permissions_to_project(contract.project)
    assert user.has_permission_on_object(
        f"core.{perm.value}_{attribute}", entities.get(attribute)
    )


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
def test_contract_entity_permissions(permissions, group):
    """
    Tests user permissions on Contract and related chidren entities based on User status

    FIXTURE:
        permissions: Needed to load default permissions

    PARAMETERS:
        group: The group the user belongs to
    """
    user = UserFactory(groups=[group()])
    user.save()
    contract = ContractFactory()
    contract.save()

    document = ContractDocumentFactory(object_id=contract.pk)
    document.save()

    if user.is_part_of(DataStewardGroup(), LegalGroup()):
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", document
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", contract
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract",
            contract.partner_roles[0],
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_contract", document
        )

    else:
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", document
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", contract
        )
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract",
            contract.partner_roles[0],
        )

        contract.local_custodians.set([user])
        contract.save()
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", contract
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract", document
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_contract",
            contract.partner_roles[0],
        )
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.PROTECTED.value}_contract", document
        )


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize(
    "entity_factory",
    [
        AccessFactory,
        DataLocationFactory,
        LegalBasisFactory,
        ShareFactory,
        DatasetDocumentFactory,
    ],
)
def test_dataset_entity_permissions(permissions, group, entity_factory):
    """
    Tests user permissions on Dataset and related chidren entities based on User status

    FIXTURE:
        permissions: Needed to load default permissions

    PARAMETERS:
        group: The group the user belongs to
    """
    user = UserFactory(groups=[group()])
    user.save()
    project = ProjectFactory()
    project.save()
    dataset = DatasetFactory(title="Test", project=project)
    dataset.save()

    new_entity = (
        entity_factory(object_id=dataset.pk)
        if entity_factory == DatasetDocumentFactory
        else entity_factory(dataset=dataset)
    )

    new_entity.save()

    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_dataset", new_entity
        )
    else:
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_dataset", new_entity
        )

        dataset.local_custodians.set([user])
        dataset.save()
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_dataset", new_entity
        )


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize("entity_factory", [ProjectDocumentFactory])
def test_project_entity_permissions(permissions, group, entity_factory):
    """
    Tests user permissions on Project and related chidren entities based on User status

    FIXTURE:
        permissions: Needed to load default permissions

    PARAMETERS:
        group: The group the user belongs to
    """
    user = UserFactory(groups=[group()])
    user.save()
    project = ProjectFactory(title="Test")
    project.save()

    new_entity = entity_factory(object_id=project.pk)
    new_entity.save()

    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_project", new_entity
        )
    else:
        assert not user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_project", new_entity
        )

        project.local_custodians.set([user])
        project.save()
        assert user.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_project", new_entity
        )
