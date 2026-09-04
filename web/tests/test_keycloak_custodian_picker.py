from unittest.mock import patch

from django.shortcuts import reverse

from core.forms.dataset import DatasetForm
from core.synchronizers import OIDCUser
from core.models import Access, User
from test.factories import (
    AccessFactory,
    ContactFactory,
    DataStewardGroup,
    DatasetFactory,
    UserFactory,
    VIPGroup,
)


def keycloak_account(
    oidc_id="keycloak-id",
    email="person@example.org",
    username="person.example",
):
    return {
        "email": email,
        "firstName": "Person",
        "lastName": "Example",
        "username": username,
        "emailVerified": True,
    }


def lookup_as_steward(client):
    client.force_login(UserFactory(groups=[DataStewardGroup()]))
    return client


@patch("web.views.keycloak.KeycloakBackend")
def test_lookup_returns_bound_daisy_user_without_calling_keycloak(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id="keycloak-id")
    lookup_as_steward(client)

    response = client.get(reverse("keycloak_custodian_lookup"), {"email": user.email})

    assert response.json()["results"] == [
        {
            "id": str(user.id),
            "text": f"{user.get_full_name()} ({user.email})",
            "is_active": True,
        }
    ]
    mock_backend.assert_not_called()


@patch("web.views.keycloak.KeycloakBackend")
def test_lookup_falls_back_to_keycloak_case_insensitively_for_unbound_user(
    mock_backend, client
):
    UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_users_by_email.return_value = [
        OIDCUser("keycloak-id", "person@example.org", "Person", "Example")
    ]
    lookup_as_steward(client)

    response = client.get(
        reverse("keycloak_custodian_lookup"), {"email": "PERSON@EXAMPLE.ORG"}
    )

    mock_backend.return_value.get_users_by_email.assert_called_once_with(
        "person@example.org"
    )
    assert response.json()["results"][0]["id"] == "keycloak:keycloak-id"


@patch("web.views.keycloak.KeycloakBackend")
def test_lookup_returns_no_results_when_keycloak_has_no_match(mock_backend, client):
    mock_backend.return_value.get_users_by_email.return_value = []
    lookup_as_steward(client)

    response = client.get(
        reverse("keycloak_custodian_lookup"), {"email": "none@example.org"}
    )

    assert response.json() == {"results": []}


@patch("web.views.keycloak.KeycloakBackend")
def test_lookup_returns_one_keycloak_candidate(mock_backend, client):
    mock_backend.return_value.get_users_by_email.return_value = [
        OIDCUser(
            "keycloak-id",
            "person@example.org",
            "Person",
            "Example",
            identity_provider="ldap",
        )
    ]
    lookup_as_steward(client)

    response = client.get(
        reverse("keycloak_custodian_lookup"), {"email": "person@example.org"}
    )

    assert response.json()["results"] == [
        {
            "id": "keycloak:keycloak-id",
            "text": "Person Example (person@example.org; ldap)",
            "is_active": True,
        }
    ]


@patch("web.views.keycloak.KeycloakBackend")
def test_lookup_returns_all_keycloak_candidates_with_identity_providers(
    mock_backend, client
):
    mock_backend.return_value.get_users_by_email.return_value = [
        OIDCUser(
            "first-id",
            "person@example.org",
            "Person",
            "Example",
            identity_provider="ldap",
        ),
        OIDCUser(
            "second-id",
            "person@example.org",
            "Person",
            "Example",
            identity_provider="eduGAIN",
        ),
    ]
    lookup_as_steward(client)

    response = client.get(
        reverse("keycloak_custodian_lookup"), {"email": "person@example.org"}
    )

    assert [result["text"] for result in response.json()["results"]] == [
        "Person Example (person@example.org; ldap)",
        "Person Example (person@example.org; eduGAIN)",
    ]


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_keycloak_custodian_promotes_contact(mock_backend, client):
    steward = UserFactory(groups=[DataStewardGroup()])
    client.force_login(steward)
    contact = ContactFactory(oidc_id="keycloak-id", email="person@example.org")
    access = AccessFactory(contact=contact, user=None)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 200
    user = User.objects.get(oidc_id="keycloak-id")
    assert user.username == "person.example"
    access.refresh_from_db()
    contact.refresh_from_db()
    assert access.user == user
    assert access.contact is None
    assert contact.oidc_id is None


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_removes_known_idp_suffix_from_created_username(
    mock_backend, client
):
    client.force_login(UserFactory(groups=[DataStewardGroup()]))
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account(
        username="person.example|ul"
    )

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 200
    assert User.objects.get(oidc_id="keycloak-id").username == "person.example"


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_adopts_unbound_daisy_user(mock_backend, client):
    steward = UserFactory(groups=[DataStewardGroup()])
    user = UserFactory(email="person@example.org", oidc_id=None)
    client.force_login(steward)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_rejects_inactive_daisy_user(mock_backend, client):
    steward = UserFactory(groups=[DataStewardGroup()])
    UserFactory(oidc_id="keycloak-id", is_active=False)
    client.force_login(steward)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 409
    assert response.json()["error"] == "This DAISY user is inactive."


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_rejects_email_bound_to_different_oidc_id(mock_backend, client):
    steward = UserFactory(groups=[DataStewardGroup()])
    UserFactory(email="person@example.org", oidc_id="other-id")
    client.force_login(steward)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 409
    assert response.json()["error"] == "This email is bound to another account."


@patch("web.views.keycloak.KeycloakBackend")
def test_provisioning_rejects_duplicate_daisy_email(mock_backend, client):
    steward = UserFactory(groups=[DataStewardGroup()])
    UserFactory(email="person@example.org")
    UserFactory(email="person@example.org")
    client.force_login(steward)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 409
    assert response.json()["error"] == "Multiple DAISY users share this email."


def test_dataset_form_saves_selected_user_as_local_custodian():
    vip = UserFactory(groups=[VIPGroup()])
    selected_user = UserFactory()
    dataset = DatasetFactory(local_custodians=[vip])
    form = DatasetForm(
        data={
            "title": dataset.title,
            "local_custodians": [vip.id, selected_user.id],
            "project": dataset.project.id,
            "comments": dataset.comments or "",
            "other_external_id": dataset.other_external_id or "",
        },
        instance=dataset,
    )

    assert form.is_valid(), form.errors
    form.save()
    assert selected_user in dataset.local_custodians.all()


def test_custodian_modal_script_has_search_and_selection_contract():
    script_path = "web/static/js/keycloak-custodian-picker.js"
    with open(script_path) as script:
        contents = script.read()

    assert ".keycloak-custodian-add" in contents
    assert '$.get(trigger.data("search-url")' in contents
    assert "response.results.forEach" in contents
    assert "provisionCandidate" in contents
    assert "addUser(select" in contents


def test_provisioning_keycloak_custodian_requires_data_steward(client):
    client.force_login(UserFactory())

    response = client.post(
        reverse("keycloak_custodian_provision"), {"oidc_id": "keycloak-id"}
    )

    assert response.status_code == 403
