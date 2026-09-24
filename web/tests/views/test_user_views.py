import pytest
from django.shortcuts import reverse
from django.test.client import Client

from test.factories import (
    AccessFactory,
    ContactFactory,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
    UserFactory,
)
from core.models.user import User


def check_user_views_permissions(url: str, user: User):
    client = Client()
    assert client.login(
        username=user.username,
        password="test-user" if not user.is_superuser else "password",
    ), "Login failed"

    response = client.get(url)
    if user.is_superuser:
        assert response.status_code != 403
    else:
        assert response.status_code == 403


@pytest.mark.parametrize("group", [DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    "url_name, needs_superuser",
    [
        ("users", True),
        ("users_add", True),
        ("user", True),
        ("user_delete", True),
        ("user_edit", True),
    ],
)
def test_user_views_permissions(
    permissions, user_admin, group, url_name, needs_superuser
):
    if url_name in ["users", "users_add", "users_change_password"]:
        url = reverse(url_name)
    else:
        user_target = UserFactory()
        user_target.save()
        url = reverse(url_name, kwargs={"pk": user_target.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_user_views_permissions(url, user)
    check_user_views_permissions(url, user_admin)


@pytest.mark.django_db
def test_users_list_shows_only_the_contacts_that_hold_a_subject(client):
    bound = ContactFactory(email="bound@example.org", oidc_id="subject-1")
    ContactFactory(email="plain@example.org", oidc_id=None)
    client.force_login(UserFactory(is_superuser=True))

    contacts = client.get(reverse("users")).context["contacts"]

    assert [contact.pk for contact in contacts] == [bound.pk]


@pytest.mark.django_db
def test_users_list_resolves_the_user_and_the_access_rows_of_a_contact(client):
    contact = ContactFactory(email="grantee@example.org", oidc_id="subject-1")
    user = UserFactory(oidc_id="subject-1")
    AccessFactory(contact=contact, user=None)
    client.force_login(UserFactory(is_superuser=True))

    response = client.get(reverse("users"))
    row = response.context["contacts"][0]

    assert row.user_of_subject == user
    assert row.access_count == 1
    assert f"?contact__id__exact={contact.id}" in response.content.decode()


@pytest.mark.django_db
def test_users_list_reports_a_contact_that_no_user_holds(client):
    ContactFactory(email="orphan@example.org", oidc_id="subject-1")
    client.force_login(UserFactory(is_superuser=True))

    row = client.get(reverse("users")).context["contacts"][0]

    assert row.user_of_subject is None
    assert row.access_count == 0


@pytest.mark.django_db
@pytest.mark.parametrize("integration", [True, False])
def test_the_keycloak_button_follows_the_integration(settings, client, integration):
    settings.KEYCLOAK_INTEGRATION = integration
    UserFactory(oidc_id=None)
    client.force_login(UserFactory(is_superuser=True))

    page = client.get(reverse("users")).content.decode()

    assert ("keycloak-bind" in page) is integration
    assert ("keycloak-identity-binder.js" in page) is integration
