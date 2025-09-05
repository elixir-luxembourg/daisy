import os
import pytest
from typing import Optional
from django.shortcuts import reverse
from django.test.client import Client

from test.factories import (
    VIPGroup,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
    ContractFactory,
    UserFactory,
    ContractDocumentFactory,
    PartnerRoleFactory,
    PartnerFactory,
    ContactFactory,
    GDPRRoleFactory,
    ProjectFactory,
)
from core.constants import Permissions
from core.models.user import User
from core.models.contract import Contract

from .utils import (
    check_response_status,
    check_datasteward_restricted_url,
    check_response_context_data,
)


def check_contract_view_permissions(
    url: str, user: User, action: Permissions, contract: Optional[Contract]
):
    """
    Data stewards and Legal can edit/delete all contracts.
    Other users can edit/delete contracts if they are local custodians
    """
    if action:
        if user.is_part_of(DataStewardGroup()) or (
            user.is_part_of(LegalGroup()) and action != Permissions.DELETE
        ):
            assert user.has_permission_on_object(
                f"core.{action.value}_contract", contract
            )
        else:
            assert not user.has_permission_on_object(
                f"core.{action.value}_contract", contract
            )

        check_response_status(url, user, [f"core.{action.value}_contract"], contract)
    else:
        check_response_status(url, user, [], contract)


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize(
    "url_name, perm",
    [
        ("contracts", None),
        ("contract_add", None),
        ("contract", None),
        ("add_partner_role_to_contract", Permissions.EDIT),
        ("contract_delete", Permissions.DELETE),
        ("contract_edit", Permissions.EDIT),
    ],
)
def test_contract_views_permissions(permissions, group, url_name, perm):
    """
    Tests whether users from different groups can access urls associated with Contract instances
    """
    contract = None
    if url_name in ["contracts", "contract_add", "contracts_export"]:
        url = reverse(url_name)
    else:
        contract = ContractFactory()
        contract.save()
        url = reverse(url_name, kwargs={"pk": contract.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_contract_view_permissions(url, user, perm, contract)


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
def test_contract_view_protected_documents(permissions, group):
    contract = ContractFactory()
    user = UserFactory(groups=[group()])

    client = Client()
    assert client.login(username=user.username, password="test-user"), "Login failed"

    url = reverse("contract", kwargs={"pk": contract.pk})
    response = client.get(url, follow=True)

    if user.is_part_of(VIPGroup()):
        assert b'<div class="row mt-4" id="documents-card">' not in response.content
        assert (
            b'<h2 class="card-title"><span><i class="material-icons">description</i></span> Documents</h2>'
            not in response.content
        )

        contract.local_custodians.set([user])
        response = client.get(url, follow=True)
        assert b'<div class="row mt-4" id="documents-card">' in response.content
        assert (
            b'<h2 class="card-title"><span><i class="material-icons">description</i></span> Documents</h2>'
            in response.content
        )

    else:
        assert b'<div class="row mt-4" id="documents-card">' in response.content
        assert (
            b'<h2 class="card-title"><span><i class="material-icons">description</i></span> Documents</h2>'
            in response.content
        )


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
def test_contract_edit_protected_documents(permissions, group):
    document = ContractDocumentFactory(with_file=True)
    contract = document.content_object

    user = UserFactory(groups=[group()])

    client = Client()
    assert client.login(username=user.username, password="test-user"), "Login failed"

    url = reverse("contract", kwargs={"pk": contract.pk})
    response = client.get(url, follow=True)

    if user.is_part_of(DataStewardGroup(), LegalGroup()):
        assert (
            b'<div class="ml-1 float-right btn-group" id="add-contract-document">'
            in response.content
        )
        assert (
            b'<th id="document-action-head" style="width:7em">Actions</th>'
            in response.content
        )
        assert b'<td id="document-action">' in response.content
    else:
        assert (
            b'<div class="ml-1 float-right btn-group" id="add-contract-document">'
            not in response.content
        )
        assert (
            b'<th id="document-action-head" style="width:7em">Actions</th>'
            not in response.content
        )
        assert b'<td id="document-action">' not in response.content

    if user.is_part_of(VIPGroup()):
        contract.local_custodians.set([user])
        response = client.get(url, follow=True)
        assert (
            b'<div class="ml-1 float-right btn-group" id="add-contract-document">'
            in response.content
        )
        assert (
            b'<th id="document-action-head" style="width:7em">Actions</th>'
            in response.content
        )
        assert b'<td id="document-action">' in response.content

    os.remove(document.content.name)


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, AuditorGroup, LegalGroup]
)
def test_contract_export(permissions, group):
    url = reverse("contracts_export")
    user = UserFactory(groups=[group()])
    check_datasteward_restricted_url(url, user)


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
def test_contract_views_context(permissions, group):
    user = UserFactory(groups=[group()])
    contract = ContractFactory()

    url = reverse("contract", kwargs={"pk": contract.pk})
    check_response_context_data(
        url, user, f"core.{Permissions.EDIT.value}_contract", contract, "can_edit"
    )


def test_partner_role_create_without_roles(permissions):
    """
    Test that a partner role can be created without selecting any roles
    """
    contract = ContractFactory(partners_roles=[])
    user = UserFactory(groups=[DataStewardGroup()])
    partner = PartnerFactory()
    contact = ContactFactory()

    client = Client()
    assert client.login(username=user.username, password="test-user"), "Login failed"

    url = reverse("add_partner_role_to_contract", kwargs={"pk": contract.pk})
    client.post(
        url,
        {
            "contract": contract.pk,
            "partner": partner.pk,
            "contacts": [contact.pk],
        },
        follow=True,
    )

    partner_role = contract.partners_roles.filter(partner=partner).first()
    assert partner_role.roles.count() == 0


def test_partner_role_edit_remove_roles(permissions):
    """
    Test that existing roles can be removed from a partner role
    """
    contract = ContractFactory()
    user = UserFactory(groups=[DataStewardGroup()])
    partner = PartnerFactory()
    contact = ContactFactory()
    gdpr_role = GDPRRoleFactory()

    partner_role = PartnerRoleFactory(contract=contract, partner=partner)
    partner_role.contacts.add(contact)
    partner_role.roles.add(gdpr_role)
    assert partner_role.roles.count() == 1

    client = Client()
    assert client.login(username=user.username, password="test-user"), "Login failed"

    url = reverse("edit_partner_role", kwargs={"pk": partner_role.pk})
    client.post(
        url,
        {
            "contract": contract.pk,
            "partner": partner.pk,
            "contacts": [contact.pk],
        },
        follow=True,
    )

    partner_role.refresh_from_db()
    assert partner_role.roles.count() == 0


def test_contract_display_partners_methods():
    """
    Test display_partners and display_partners_tooltip methods for different partner counts
    """
    # Test with no partners
    contract = ContractFactory()
    contract.partners_roles.all().delete()
    assert contract.display_partners() == "-"
    assert contract.display_partners_tooltip() == ""

    # One partner
    partner1 = PartnerFactory()
    PartnerRoleFactory(contract=contract, partner=partner1)
    assert contract.display_partners() == str(partner1)
    assert contract.display_partners_tooltip() == str(partner1)

    # Two partners
    partner2 = PartnerFactory()
    PartnerRoleFactory(contract=contract, partner=partner2)
    # Order may vary
    expected_two_a = f"{partner1}, {partner2}"
    expected_two_b = f"{partner2}, {partner1}"
    result_display = contract.display_partners()
    result_tooltip = contract.display_partners_tooltip()
    assert result_display in [expected_two_a, expected_two_b]
    assert result_tooltip in [expected_two_a, expected_two_b]

    # More than two partners
    partner3 = PartnerFactory()
    partner4 = PartnerFactory()
    PartnerRoleFactory(contract=contract, partner=partner3)
    PartnerRoleFactory(contract=contract, partner=partner4)

    # Check structure, not exact order
    result_display = contract.display_partners()
    result_tooltip = contract.display_partners_tooltip()

    # Should show "and 2 more..." for 4 partners
    assert "and 2 more..." in result_display

    # Tooltip should show all partners
    for partner in [partner1, partner2, partner3, partner4]:
        assert str(partner) in result_tooltip


@pytest.mark.django_db
def test_contracts_for_form(client):
    user = UserFactory()
    client.force_login(user)
    project = ProjectFactory()
    contract = ContractFactory(project=project)
    other_contract = ContractFactory(project=ProjectFactory())

    url = reverse("contracts_for_form")
    response = client.get(url)
    assert response.status_code == 200
    contract_ids = [c["id"] for c in response.json()["contracts"]]
    assert contract.pk in contract_ids
    assert other_contract.pk in contract_ids

    url += f"?projectId={project.pk}"
    response = client.get(url)
    assert response.status_code == 200
    contract_ids = [c["id"] for c in response.json()["contracts"]]
    assert contract.pk in contract_ids
    assert other_contract.pk not in contract_ids
