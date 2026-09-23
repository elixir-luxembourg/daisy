from unittest.mock import patch

import pytest
from django.shortcuts import reverse
from django.test import override_settings

from test.factories import UserFactory

END_SESSION = "https://sso.example/realms/testing/protocol/openid-connect/logout"


def logged_in_with_an_id_token(client):
    client.force_login(UserFactory())
    session = client.session
    session["oidc_id_token"] = "id-token"
    session.save()


@pytest.mark.django_db
@override_settings(OIDC_ENABLED=True)
@patch(
    "web.views.user.oauth.keycloak.server_metadata", {"issuer": "https://sso.example"}
)
def test_logout_falls_back_to_daisy_when_keycloak_has_no_end_session_endpoint(client):
    logged_in_with_an_id_token(client)

    response = client.get(reverse("logout"))

    assert response.url == reverse("login")


@pytest.mark.django_db
@override_settings(OIDC_ENABLED=True)
@patch(
    "web.views.user.oauth.keycloak.server_metadata",
    {"end_session_endpoint": END_SESSION},
)
def test_logout_ends_the_keycloak_session(client):
    logged_in_with_an_id_token(client)

    response = client.get(reverse("logout"))

    assert response.url.startswith(END_SESSION)
    assert "id_token_hint=id-token" in response.url


@pytest.mark.django_db
@override_settings(OIDC_ENABLED=True)
@patch(
    "web.views.user.oauth.keycloak.server_metadata",
    {"end_session_endpoint": END_SESSION},
)
def test_logout_ends_the_keycloak_session_of_an_anonymous_person(client):
    """A refused login is anonymous here, and it still has to leave the Keycloak session."""
    session = client.session
    session["oidc_id_token"] = "id-token"
    session.save()

    response = client.get(reverse("logout"))

    assert response.url.startswith(END_SESSION)
