from unittest.mock import patch

import pytest
from django.shortcuts import reverse

from core.forms.dataset import DatasetForm
from core.models import Access, User
from core.synchronizers import OIDCUser
from test.factories import (
    ContactFactory,
    DatasetFactory,
    UserFactory,
    VIPGroup,
)


def keycloak_account(
    oidc_id="keycloak-id",
    email="person@example.org",
    username="person.example",
    identity_provider=None,
):
    return OIDCUser(
        id=oidc_id,
        email=email,
        first_name="Person",
        last_name="Example",
        username=username,
        identity_provider=identity_provider,
    )


def as_superuser(client):
    client.force_login(UserFactory(is_superuser=True))
    return client


def candidates_url(user):
    return reverse("keycloak_candidates", kwargs={"pk": user.pk})


def bind_url(user):
    return reverse("keycloak_bind_identity", kwargs={"pk": user.pk})


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_candidates_list_every_keycloak_account_of_the_email(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_users_by_email.return_value = [
        keycloak_account("first-id", identity_provider="University of Luxembourg"),
        keycloak_account("second-id", identity_provider="ORCID"),
    ]
    as_superuser(client)

    response = client.get(candidates_url(user))

    mock_backend.return_value.get_users_by_email.assert_called_once_with(
        "person@example.org"
    )
    assert [result["id"] for result in response.json()["results"]] == [
        "first-id",
        "second-id",
    ]
    assert response.json()["results"][1]["text"].endswith("ORCID)")


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_candidates_fall_back_to_the_username_without_a_known_provider(
    mock_backend, client
):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_users_by_email.return_value = [keycloak_account()]
    as_superuser(client)

    response = client.get(candidates_url(user))

    assert response.json()["results"][0]["text"].endswith("person.example)")


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_candidates_are_empty_when_keycloak_has_no_match(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_users_by_email.return_value = []
    as_superuser(client)

    response = client.get(candidates_url(user))

    assert response.json() == {"results": []}


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_candidates_are_refused_for_a_user_that_has_an_oidc_id(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id="keycloak-id")
    as_superuser(client)

    response = client.get(candidates_url(user))

    assert response.status_code == 409
    assert response.json()["error"] == "This user already has an OIDC ID."
    mock_backend.assert_not_called()


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_stores_the_selected_oidc_id(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()
    as_superuser(client)

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 200
    assert response.json()["user"]["oidc_id"] == "keycloak-id"
    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_creates_no_user_and_moves_no_access(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()
    as_superuser(client)
    users_before = User.objects.count()

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 200
    assert User.objects.count() == users_before
    assert Access.objects.count() == 0


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_refuses_an_account_that_belongs_to_a_contact(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    ContactFactory(oidc_id="keycloak-id", email="person@example.org")
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()
    as_superuser(client)

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 409
    assert response.json()["error"].startswith(
        "This Keycloak account belongs to a contact in DAISY."
    )
    user.refresh_from_db()
    assert user.oidc_id is None


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_refuses_an_account_used_by_another_user(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    UserFactory(email="other@example.org", oidc_id="keycloak-id")
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()
    as_superuser(client)

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 409
    assert (
        response.json()["error"]
        == "This Keycloak account is already used by another user."
    )
    user.refresh_from_db()
    assert user.oidc_id is None


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_refuses_an_account_with_another_email(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id=None)
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account(
        email="somebody.else@example.org"
    )
    as_superuser(client)

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 409
    assert response.json()["error"] == "This Keycloak account has another email."
    user.refresh_from_db()
    assert user.oidc_id is None


@pytest.mark.django_db
@patch("web.views.keycloak.KeycloakBackend")
def test_binding_is_refused_for_a_user_that_has_an_oidc_id(mock_backend, client):
    user = UserFactory(email="person@example.org", oidc_id="other-id")
    mock_backend.return_value.get_external_user_info.return_value = keycloak_account()
    as_superuser(client)

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 409
    user.refresh_from_db()
    assert user.oidc_id == "other-id"


@pytest.mark.django_db
def test_candidates_require_a_superuser(client):
    user = UserFactory(oidc_id=None)
    client.force_login(UserFactory())

    assert client.get(candidates_url(user)).status_code == 403


@pytest.mark.django_db
def test_binding_requires_a_superuser(client):
    user = UserFactory(oidc_id=None)
    client.force_login(UserFactory())

    response = client.post(bind_url(user), {"oidc_id": "keycloak-id"})

    assert response.status_code == 403


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


def test_binder_script_has_the_lookup_and_bind_contract():
    with open("web/static/js/keycloak-identity-binder.js") as script:
        contents = script.read()

    assert ".keycloak-bind" in contents
    assert '$.get(trigger.data("candidates-url")' in contents
    assert "response.results.forEach" in contents
    assert "bindIdentity" in contents
    assert 'trigger.data("bind-url")' in contents
