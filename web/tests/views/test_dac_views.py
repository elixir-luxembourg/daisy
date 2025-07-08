import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission

from core.models import DAC, DacMembership
from test.factories import (
    DACFactory,
    ContractFactory,
    UserFactory,
    ContactFactory,
    DatasetFactory,
    ExposureFactory,
    DataStewardGroup,
)


@pytest.mark.django_db
def test_dac_create(client):
    user = UserFactory()
    user.user_permissions.add(Permission.objects.get(codename="change_contract"))
    client.force_login(user)
    contract = ContractFactory()
    custodian = UserFactory()
    # DAC creation form
    response = client.get(reverse("dacs"))
    assert response.status_code == 200
    # Create new DACs
    url = reverse("dac_add")
    for dac_name in ("Test DAC", "Another Test DAC"):
        data = {
            "title": dac_name,
            "projects": contract.project.pk,
            "contract": contract.pk,
            "local_custodians": [custodian.pk],
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert DAC.objects.filter(title=dac_name).exists()
    # User without permissions
    no_perm_user = UserFactory()
    client.force_login(no_perm_user)
    data = {
        "title": "DAC for user without permissions",
        "projects": contract.project.pk,
        "contract": contract.pk,
        "local_custodians": [custodian.pk],
    }
    response = client.post(reverse("dac_add"), data)
    assert response.status_code == 403


@pytest.mark.django_db
def test_dac_detail(client):
    user = UserFactory()
    user.user_permissions.add(
        Permission.objects.get(codename="change_dac")
    )  # for edit DAC button
    client.force_login(user)
    dac = DACFactory()
    url = reverse("dac", args=[dac.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert "memberships" in response.context
    assert "local_custodians" in response.context
    assert "datasets" in response.context
    assert "can_edit" in response.context


@pytest.mark.django_db
def test_dac_edit(client):
    user = UserFactory()
    user.user_permissions.add(Permission.objects.get(codename="change_contract"))
    client.force_login(user)

    dac = DACFactory()
    url = reverse("dac_edit", args=[dac.pk])
    # DAC edit form
    response = client.get(url)
    assert response.status_code == 200
    # Edit remark or other editable field
    data = {
        "title": dac.title,
        "projects": dac.contract.project.pk,
        "contract": dac.contract.pk,
        "local_custodians": [u.pk for u in dac.local_custodians.all()],
    }
    response = client.post(url, data)
    assert response.status_code == 200
    # User without permissions
    no_perm_user = UserFactory()
    client.force_login(no_perm_user)
    response = client.post(url, data)
    assert response.status_code == 403


@pytest.mark.django_db
def test_dac_list(client):
    user = UserFactory()
    client.force_login(user)
    DACFactory(title="DAC 1")
    DACFactory(title="DAC 2")
    url = reverse("dacs")
    response = client.get(url, {"search": "1"})
    assert "DAC 1" in response.content.decode()
    response = client.get(url, {"ordering": "title"})
    assert response.status_code == 200


@pytest.mark.django_db
def test_add_dac_to_contract(client):
    user = UserFactory()
    user.user_permissions.add(Permission.objects.get(codename="change_contract"))
    client.force_login(user)

    contract = ContractFactory()
    custodian = UserFactory()
    url = reverse("add_dac_to_contract", args=[contract.pk])
    data = {
        "title": "DAC for Contract",
        "projects": contract.project.pk,
        "contract": contract.pk,
        "local_custodians": [custodian.pk],
    }
    response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 200
    assert DAC.objects.filter(title="DAC for Contract", contract=contract).exists()


@pytest.mark.django_db
def test_pick_member_for_dac_and_remove_member(client):
    """
    Test adding and removing a member from a DAC.
    """
    user = UserFactory()
    user.user_permissions.add(Permission.objects.get(codename="change_dac"))
    client.force_login(user)
    dac = DACFactory()
    contact = ContactFactory()
    # Add member
    pick_url = reverse("pick_member_for_dac", args=[dac.pk])
    response = client.post(pick_url, {"contact": contact.pk})
    assert response.status_code == 302
    assert response.url == reverse("dac", args=[dac.pk])
    assert DacMembership.objects.filter(dac=dac, contact=contact).exists()
    # Remove member
    remove_url = reverse("remove_member_from_dac", args=[dac.pk, contact.pk])
    response = client.delete(remove_url)
    assert response.status_code == 200
    assert not DacMembership.objects.filter(dac=dac, contact=contact).exists()


@pytest.mark.django_db
def test_pick_dataset_for_dac_permission(client):
    """
    Test the permission for picking a dataset for a DAC.
    """
    user_datasteward = UserFactory(groups=[DataStewardGroup()])
    client.force_login(user_datasteward)
    assert user_datasteward.is_data_steward

    dac = DACFactory()
    dataset = DatasetFactory()
    ExposureFactory(dataset=dataset)
    assert dataset.is_published
    assert not dataset.dac

    url = reverse("pick_dataset_for_dac", args=[dac.pk])
    response = client.post(url, {"dataset": dataset.pk})
    assert response.status_code == 302

    # User without Data Steward permission
    user = UserFactory()
    client.force_login(user)
    assert not user.is_data_steward
    response = client.post(url, {"dataset": dataset.pk})
    assert response.status_code == 403
