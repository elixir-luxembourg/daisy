import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.forms import DACForm, DACFormEdit
from core.models import DacMembership
from test.factories import (
    DACFactory,
    DatasetFactory,
    ContractFactory,
    ProjectFactory,
    UserFactory,
    ContactFactory,
)
import datetime


# MODELS TESTS
@pytest.mark.django_db
def test_dac_creation():
    contract = ContractFactory()
    custodian = UserFactory()
    dac = DACFactory(contract=contract, local_custodians=[custodian], title="Test DAC")
    assert dac.title == "Test DAC"
    assert str(dac) == "Test DAC"
    assert dac.contract == contract
    assert custodian in dac.local_custodians.all()


@pytest.mark.django_db
def test_dac_requires_local_custodian():
    contract = ContractFactory()
    custodian = UserFactory()
    dac = DACFactory(
        contract=contract, local_custodians=[custodian], title="No Custodian DAC"
    )
    with pytest.raises(ValidationError) as exc:
        dac.local_custodians.clear()
        dac.full_clean()
    assert "At least one local custodian is required." in str(exc.value)


@pytest.mark.django_db
def test_dac_get_absolute_url_and_full_url(settings):
    contract = ContractFactory()
    custodian = UserFactory()
    dac = DACFactory(contract=contract, local_custodians=[custodian])
    url = dac.get_absolute_url()
    assert url.endswith(f"/dac/{dac.pk}/")
    settings.SERVER_SCHEME = "http"
    settings.SERVER_URL = "testserver"
    full_url = dac.get_full_url()
    assert full_url.startswith("http://testserver")


@pytest.mark.django_db
def test_dac_to_dict():
    contract = ContractFactory()
    custodian = UserFactory()
    dac = DACFactory(contract=contract, local_custodians=[custodian])
    d = dac.to_dict()
    assert d["title"] == dac.title
    assert d["contract"]["id"] == contract.id
    assert len(d["local_custodians"]) == 1


@pytest.mark.django_db
def test_dac_membership_unique_constraint():
    dac = DACFactory()
    contact = ContactFactory()
    DacMembership.objects.create(dac=dac, contact=contact, remark="First")
    with pytest.raises(IntegrityError):
        DacMembership.objects.create(dac=dac, contact=contact, remark="Duplicate")


@pytest.mark.django_db
def test_dac_members_property_and_project_property():
    contract = ContractFactory()
    custodian = UserFactory()
    dac = DACFactory(contract=contract, local_custodians=[custodian])
    assert dac.project == contract.project
    assert hasattr(dac, "datasets")


@pytest.mark.django_db
def test_dac_cannot_be_deleted():
    dac = DACFactory()
    with pytest.raises(ValidationError) as exc:
        dac.delete()
    assert "cannot be deleted" in str(exc.value)


@pytest.mark.django_db
def test_dac_datasets_property_returns_related_datasets():
    dac = DACFactory()
    dataset1 = DatasetFactory(dac=dac)
    dataset2 = DatasetFactory(dac=dac)
    datasets = dac.datasets.all() if hasattr(dac, "datasets") else dac.dataset_set.all()
    assert dataset1 in datasets
    assert dataset2 in datasets
    assert datasets.count() == 2


@pytest.mark.django_db
def test_cannot_remove_dac_from_dataset():
    dac = DACFactory()
    dataset = DatasetFactory(dac=dac)
    dataset.dac = None
    with pytest.raises(ValidationError) as exc:
        dataset.full_clean()
    assert "You cannot change the DAC once it is set." in str(exc.value)


@pytest.mark.django_db
def test_dacmembership_has_added_and_remark_fields():
    dac = DACFactory()
    contact = ContactFactory()
    remark = "Test remark"
    membership = DacMembership.objects.create(dac=dac, contact=contact, remark=remark)
    assert hasattr(membership, "added")
    assert isinstance(membership.added, datetime.datetime)
    assert hasattr(membership, "remark")
    assert membership.remark == remark


# FORMS TESTS
@pytest.mark.django_db
def test_dacform_contract_must_belong_to_selected_project():
    project = ProjectFactory()
    wrong_project = ProjectFactory()
    contract = ContractFactory(project=project)
    custodian = UserFactory()
    form = DACForm(
        data={
            "title": "Test DAC",
            "projects": wrong_project.pk,
            "contract": contract.pk,
            "local_custodians": [custodian.pk],
        }
    )
    assert not form.is_valid()
    assert "contract" in form.errors
    assert (
        "Selected contract does not belong to the selected project."
        in form.errors["contract"]
    )


@pytest.mark.django_db
def test_dacform_initial_values_and_choices():
    project = ProjectFactory()
    contract = ContractFactory(project=project)
    form = DACForm(contract_id=contract.id)
    # Should set initial contract and project
    assert form.fields["contract"].initial == contract.id
    assert form.fields["projects"].initial == project.id
    # Choices should be limited to the provided contract/project
    assert (contract.id, str(contract)) in form.fields["contract"].choices
    assert (project.id, str(project)) in form.fields["projects"].choices


@pytest.mark.django_db
def test_dacformedit_fields_disabled_and_initials():
    project = ProjectFactory()
    contract = ContractFactory(project=project)
    custodian = UserFactory()
    dac = DACFactory(contract=contract, local_custodians=[custodian])
    form = DACFormEdit(instance=dac)
    # Fields should be disabled
    assert form.fields["projects"].disabled
    assert form.fields["contract"].disabled
    assert form.fields["title"].disabled
    # Initial values should be set correctly
    assert form.fields["projects"].initial == contract.project.id
