from unittest.mock import patch

import pytest
from django.shortcuts import reverse
from django.test import override_settings

from core.models import User
from test.factories import ContactFactory, UserFactory

CLIENT_ID = "daisy-client"


def oidc_token(
    oidc_id="oidc-id",
    email="person@example.org",
    username="person.example|ul",
    roles=None,
    client_id=CLIENT_ID,
):
    userinfo = {
        "sub": oidc_id,
        "email": email,
        "username": username,
        "given_name": "Person",
        "family_name": "Example",
    }
    if roles is not None:
        userinfo["resource_access"] = {client_id: {"roles": roles}}
    return {"id_token": "id-token", "userinfo": userinfo}


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
def test_auth_creates_a_new_user_instead_of_adopting_an_inactive_one(client):
    """A login never adopts and never activates an inactive record."""
    inactive = UserFactory(oidc_id=None, email="person@example.org", is_active=False)

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    inactive.refresh_from_db()
    assert inactive.oidc_id is None
    assert not inactive.is_active
    created = User.objects.get(oidc_id="oidc-id")
    assert created.pk != inactive.pk
    assert created.username == "person.example|ul"
    assert created.is_active


@pytest.mark.django_db
def test_auth_activates_an_inactive_user_of_the_subject(client):
    user = UserFactory(oidc_id="oidc-id", email="person@example.org", is_active=False)

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    assert client.session["_auth_user_id"] == str(user.id)
    user.refresh_from_db()
    assert user.is_active
    assert User.objects.filter(oidc_id="oidc-id").count() == 1


@pytest.mark.django_db
def test_auth_creates_a_user_for_a_second_identity_of_the_same_email(client):
    """
    Two Keycloak accounts on one email are two users now, and nobody is locked out.
    The oidc_id of the first one is immutable.
    """
    bound = UserFactory(oidc_id="other-id", email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    bound.refresh_from_db()
    assert bound.oidc_id == "other-id"
    created = User.objects.get(oidc_id="oidc-id")
    assert created.pk != bound.pk
    assert created.email == "person@example.org"


@pytest.mark.django_db
def test_auth_refuses_when_several_active_users_share_the_email(client):
    """Nothing says which record is the person, a data steward decides."""
    first = UserFactory(oidc_id=None, email="person@example.org")
    second = UserFactory(oidc_id=None, email="PERSON@EXAMPLE.ORG")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.oidc_id is None
    assert second.oidc_id is None
    assert not User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
def test_auth_creates_a_user_although_a_contact_has_the_email(client):
    """A contact is a record, not an identity, and it does not block a login."""
    contact = ContactFactory(email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    assert User.objects.filter(oidc_id="oidc-id").exists()
    contact.refresh_from_db()
    assert contact.oidc_id is None


@pytest.mark.django_db
def test_auth_creates_a_user_although_a_contact_holds_the_subject(client):
    """A subject becomes a user, the contact keeps its access records until a migration."""
    contact = ContactFactory(oidc_id="oidc-id", email="person@example.org")

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    assert User.objects.filter(oidc_id="oidc-id").exists()
    contact.refresh_from_db()
    assert contact.oidc_id == "oidc-id"


@pytest.mark.django_db
def test_auth_creates_active_user_when_identity_is_unclaimed(client):
    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    user = User.objects.get(oidc_id="oidc-id")
    assert user.username == "person.example|ul"
    assert user.is_active
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_auth_refuses_when_an_older_row_holds_the_keycloak_username(client):
    """A username is unique. The row belongs to another email, so a steward has to fix it."""
    UserFactory(username="person.example|ul", email="other@example.org", oidc_id=None)

    response = authenticate(client, oidc_token())

    assert response.url == reverse("login")
    assert not User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username", ["person.example|ul", "person.example|orcid", "person.example"]
)
def test_auth_accepts_every_identity_provider(client, username):
    """Nothing filters on the identity provider."""
    response = authenticate(client, oidc_token(username=username))

    assert response.url == reverse("dashboard")
    assert User.objects.get(oidc_id="oidc-id").username == username


@pytest.mark.django_db
def test_auth_adopts_an_unbound_user_whatever_the_identity_provider(client):
    user = UserFactory(oidc_id=None, email="person@example.org")

    response = authenticate(client, oidc_token(username="person.example|orcid"))

    assert response.url == reverse("dashboard")
    user.refresh_from_db()
    assert user.oidc_id == "oidc-id"


@pytest.mark.django_db
def test_auth_keeps_an_inactive_row_of_another_subject_inactive(client):
    other = UserFactory(oidc_id="other-id", email="other@example.org", is_active=False)

    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    other.refresh_from_db()
    assert not other.is_active


@pytest.mark.django_db
def test_auth_handles_failed_token_exchange(client):
    with patch(
        "web.views.user.oauth.keycloak.authorize_access_token",
        side_effect=RuntimeError,
    ):
        response = client.get(reverse("auth"))

    assert response.url == reverse("login")


@pytest.mark.django_db
def test_auth_logs_in_without_a_role_when_none_is_required(client):
    """The default allows every account of the realm."""
    response = authenticate(client, oidc_token())

    assert response.url == reverse("dashboard")
    assert User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
@override_settings(OIDC_REQUIRED_ROLE="daisy")
def test_auth_logs_in_with_the_required_client_role(client):
    with patch("web.views.user.oauth.keycloak.client_id", CLIENT_ID):
        response = authenticate(client, oidc_token(roles=["daisy", "other"]))

    assert response.url == reverse("dashboard")
    assert User.objects.filter(oidc_id="oidc-id").exists()


@pytest.mark.django_db
@override_settings(OIDC_REQUIRED_ROLE="daisy")
@pytest.mark.parametrize("roles", [None, [], ["other"]])
def test_auth_refuses_a_login_without_the_required_role(client, roles):
    """Nothing is created for a person that may not use DAISY."""
    with patch("web.views.user.oauth.keycloak.client_id", CLIENT_ID):
        response = authenticate(client, oidc_token(roles=roles))

    assert response.url == reverse("login")
    assert not User.objects.filter(oidc_id="oidc-id").exists()
    # the Keycloak session can still be ended, so the person can try another account
    assert client.session["oidc_id_token"] == "id-token"


@pytest.mark.django_db
@override_settings(OIDC_REQUIRED_ROLE="daisy")
def test_auth_ignores_the_roles_of_another_client(client):
    with patch("web.views.user.oauth.keycloak.client_id", CLIENT_ID):
        response = authenticate(client, oidc_token(roles=["daisy"], client_id="other"))

    assert response.url == reverse("login")
    assert not User.objects.filter(oidc_id="oidc-id").exists()
