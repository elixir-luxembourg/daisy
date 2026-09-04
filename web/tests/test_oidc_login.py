from unittest.mock import patch

import pytest
from django.shortcuts import reverse

from core.models import User
from test.factories import ContactFactory, UserFactory


def oidc_token(
    oidc_id="oidc-id",
    email="person@example.org",
    username="person.example",
):
    return {
        "id_token": "id-token",
        "userinfo": {
            "sub": oidc_id,
            "email": email,
            "preferred_username": username,
            "given_name": "Person",
            "family_name": "Example",
        },
    }


def authenticate(client, token):
    with patch(
        "web.views.user.oauth.keycloak.authorize_access_token", return_value=token
    ):
        return client.get(reverse("auth"))


@pytest.mark.django_db
def test_auth_logs_in_active_user_with_matching_oidc_id(client):
    user = UserFactory(oidc_id="oidc-id", email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    assert client.session["_auth_user_id"] == str(user.id)


@pytest.mark.django_db
def test_auth_adopts_active_unbound_user_by_case_insensitive_email(client):
    user = UserFactory(oidc_id=None, email="person@example.org")

    response = authenticate(client, oidc_token(email="PERSON@EXAMPLE.ORG"))

    assert response.url == reverse("dashboard")
    user.refresh_from_db()
    assert user.oidc_id == "oidc-id"


@pytest.mark.django_db
def test_auth_rejects_email_bound_to_another_oidc_id(client):
    user = UserFactory(oidc_id="other-id", email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    user.refresh_from_db()
    assert user.oidc_id == "other-id"
    assert not User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
def test_auth_rejects_email_claimed_by_contact(client):
    ContactFactory(email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    assert not User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
def test_auth_rejects_oidc_id_claimed_by_contact(client):
    ContactFactory(oidc_id="oidc-id", email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    assert not User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
def test_auth_creates_active_user_when_identity_is_unclaimed(client):
    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    user = User.objects.get(oidc_id="oidc-id")
    assert user.username == "person.example"
    assert user.is_active
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_auth_removes_known_idp_suffix_from_created_username(client):
    response = authenticate(client, oidc_token(username="person.example|ul"))

    assert response.url == reverse("dashboard")
    assert User.objects.get(oidc_id="oidc-id").username == "person.example"


@pytest.mark.django_db
def test_auth_rejects_inactive_user(client):
    UserFactory(oidc_id="oidc-id", is_active=False)

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_auth_handles_failed_token_exchange(client):
    with patch(
        "web.views.user.oauth.keycloak.authorize_access_token",
        side_effect=RuntimeError,
    ):
        response = client.get(reverse("auth"))

    assert response.url == reverse("login")
