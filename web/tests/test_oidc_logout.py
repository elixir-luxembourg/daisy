from unittest.mock import patch

import pytest
from django.shortcuts import reverse

from test.factories import UserFactory


@pytest.mark.django_db
@patch(
    "web.views.user.oauth.keycloak.server_metadata", {"issuer": "https://sso.example"}
)
@pytest.mark.override_settings(OIDC_ENABLED=True)
def test_logout_falls_back_to_daisy_when_keycloak_has_no_end_session_endpoint(client):
    client.force_login(UserFactory())
    session = client.session
    session["oidc_id_token"] = "id-token"
    session.save()

    response = client.get(reverse("logout"))

    assert response.url == reverse("login")
