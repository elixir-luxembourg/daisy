import pytest
from core.models import (
    Dataset,
    DataDeclaration,
    DataLocation,
    LegalBasisType,
    LegalBasis,
    Access,
)
from test.factories import (
    UserFactory,
    VIPGroup,
    StorageResourceFactory,
    DatasetFactory,
    ExposureFactory,
)
from django.urls import reverse
from django.test import Client


def test_get_dataset_add(client_user_normal):
    """
    Test view for adding dataset
    """
    pass
    # url = reverse('dataset_wizard')
    # response = client_user_normal.get(url, )
    # assert response.status_code == 302, "should redirect to first wizard step"


@pytest.mark.django_db
@pytest.mark.parametrize("data_declaration_skip", [True, False])
@pytest.mark.parametrize("storage_location_skip", [True, False])
@pytest.mark.parametrize("legal_basis_skip", [True, False])
@pytest.mark.parametrize("access_skip", [True, False])
def test_dataset_wizard_form(
    client_user_normal: Client,
    data_declaration_skip: bool,
    storage_location_skip: bool,
    legal_basis_skip: bool,
    access_skip: bool,
) -> None:
    """
    Test the behavior of the dataset wizard form in various scenarios.

    The test checks the dataset wizard form's behavior based on different combinations
    of skipping steps. The main objective is to verify that the data gets saved correctly
    when the form is submitted with different values for each step's skip option.

    Parameters:
    - client_user_normal (Client): A Django test client instance with a user session.
    - data_declaration_skip (bool): Whether the data declaration step should be skipped.
    - storage_location_skip (bool): Whether the storage location step should be skipped.
    - legal_basis_skip (bool): Whether the legal basis step should be skipped.
    - access_skip (bool): Whether the access step should be skipped.

    Asserts:
    - The number of saved model instances matches the expected count based on the skip parameters.
    - The redirect URL after the final step matches the expected URL for the created dataset.
    - The relationships between the created dataset and other objects (like data declarations,
      data locations, etc.) are correctly established.
    """
    vip_user = UserFactory.create(
        groups=[VIPGroup()], first_name="Rebecca", last_name="Kafe"
    )
    storage_backend = StorageResourceFactory.create(
        name="test_backend", managed_by="test"
    )
    legal_basis_type = LegalBasisType(name="test_legal_basis", code="test")
    legal_basis_type.save()

    wizard_test_data = {
        "dataset": [
            {
                "dataset-local_custodians": [vip_user.id],
                "dataset-title": ["Hello Dataset"],
                "dataset-project": [],
                "dataset-comments": ["A comment"],
                "dataset_wizard_view-current_step": ["dataset"],
            },
            Dataset,
        ],
        "data_declaration": [
            {
                "data_declaration-title": ["Data declaration title"],
                "data_declaration-type": ["2"],
                "comment": ["Other provenance"],
                "dataset_wizard_view-current_step": ["data_declaration"],
                "data_declaration-skip_wizard": [data_declaration_skip],
            },
            DataDeclaration,
        ],
        "storage_location": [
            {
                "storage_location-category": ["master"],
                "storage_location-backend": [storage_backend.id],
                "storage_location-data_declarations": [],
                "storage_location-datatypes": [],
                "storage_location-location_description": ["hello"],
                "dataset_wizard_view-current_step": ["storage_location"],
                "storage_location-skip_wizard": [storage_location_skip],
            },
            DataLocation,
        ],
        "legal_basis": [
            {
                "legal_basis-data_declarations": [],
                "legal_basis-legal_basis_types": [legal_basis_type.id],
                "legal_basis-personal_data_types": [],
                "legal_basis-remarks": ["Legal basis comment"],
                "dataset_wizard_view-current_step": ["legal_basis"],
                "legal_basis-skip_wizard": [legal_basis_skip],
            },
            LegalBasis,
        ],
        "access": [
            {
                "access-contact": [],
                "access-user": [vip_user.id],
                "access-project": [""],
                "access-granted_on": [""],
                "access-grant_expires_on": [""],
                "access-access_notes": ["ssq"],
                "dataset_wizard_view-current_step": ["access"],
                "access-skip_wizard": [access_skip],
            },
            Access,
        ],
    }

    for step_name, step_data in wizard_test_data.items():
        form_data, Model = step_data
        assert Model.objects.all().count() == 0
        response = client_user_normal.post(reverse("wizard"), form_data)

        if step_name != "dataset":
            skip_wizard_value = form_data[f"{step_name}-skip_wizard"][0]
            if skip_wizard_value:
                assert Model.objects.all().count() == 0
            else:
                assert Model.objects.all().count() == 1

        if step_name == "access":
            dataset = Dataset.objects.get(title="Hello Dataset")
            redirect_url = response.url
            expected_url = reverse("dataset", kwargs={"pk": dataset.id})
            assert redirect_url == expected_url

    dataset = Dataset.objects.get(title="Hello Dataset")
    assert (
        dataset.data_declarations.all().count() == DataDeclaration.objects.all().count()
    )
    assert dataset.data_locations.all().count() == DataLocation.objects.all().count()
    assert (
        dataset.legal_basis_definitions.all().count()
        == LegalBasis.objects.all().count()
    )
    assert dataset.accesses.all().count() == Access.objects.all().count()


@pytest.mark.django_db
def test_dataset_publication_status_no_exposures():
    """Test publication_status returns empty string when no exposures exist"""
    dataset = DatasetFactory.create()
    assert dataset.publication_status == ""
    assert dataset.is_published is False


@pytest.mark.django_db
def test_dataset_publication_status_with_active_exposures():
    """Test publication_status returns 'published' when active exposures exist"""
    dataset = DatasetFactory.create()
    ExposureFactory.create(dataset=dataset, is_deprecated=False)
    assert dataset.publication_status == "published"
    assert dataset.is_published is True


@pytest.mark.django_db
def test_dataset_publication_status_with_deprecated_exposures():
    """Test publication_status returns 'deprecated' when only deprecated exposures exist"""
    dataset = DatasetFactory.create()
    ExposureFactory.create(dataset=dataset, is_deprecated=True)
    assert dataset.publication_status == "deprecated"
    assert dataset.is_published is False


@pytest.mark.django_db
def test_dataset_publication_status_with_mixed_exposures():
    """Test publication_status returns 'published' when both active and deprecated exposures exist"""
    dataset = DatasetFactory.create()
    ExposureFactory.create(dataset=dataset, is_deprecated=False)
    ExposureFactory.create(dataset=dataset, is_deprecated=True)
    assert dataset.publication_status == "published"
    assert dataset.is_published is True
