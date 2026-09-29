from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from core.constants import IdentityProvider
from core.models.user import User
from core.synchronizers import OIDCUser
from test.factories import ContactFactory, UserFactory


def keycloak_user(
    oidc_id="keycloak-id",
    email="person@example.org",
    username="person.example|ul",
    identity_provider=IdentityProvider.UL,
    enabled=True,
):
    return OIDCUser(
        id=oidc_id,
        email=email,
        first_name="Person",
        last_name="Example",
        username=username,
        identity_provider=identity_provider,
        enabled=enabled,
    )


def run_import(keycloak_users, *args):
    # .env.test keeps the integration off
    with override_settings(KEYCLOAK_INTEGRATION=True), patch(
        "core.management.commands.import_keycloak_users.KeycloakBackend"
    ) as backend:
        backend.return_value.get_list_of_users.return_value = keycloak_users
        output = StringIO()
        call_command("import_keycloak_users", *args, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
@override_settings(KEYCLOAK_INTEGRATION=False)
@patch("core.management.commands.import_keycloak_users.KeycloakBackend")
def test_import_does_nothing_without_the_integration(backend):
    """The scheduled task and /api/keycloak/force both land here."""
    output = StringIO()
    call_command("import_keycloak_users", stdout=output)

    assert "The Keycloak integration is off" in output.getvalue()
    backend.assert_not_called()
    assert not User.objects.exclude(oidc_id=None).exists()


@pytest.mark.django_db
def test_import_creates_a_user_with_the_keycloak_username_and_no_password():
    output = run_import([keycloak_user()])

    user = User.objects.get(oidc_id="keycloak-id")
    assert user.username == "person.example|ul"
    assert user.email == "person@example.org"
    assert user.first_name == "Person"
    assert user.last_name == "Example"
    assert user.is_active
    assert not user.has_usable_password()
    assert output.splitlines() == ["Created 1 user(s)."]


@pytest.mark.django_db
def test_import_creates_one_user_per_identity_of_the_same_email():
    run_import(
        [
            keycloak_user("ul-id", username="person.example|ul"),
            keycloak_user(
                "orcid-id",
                username="person.example|orcid",
                identity_provider=IdentityProvider.ORCID,
            ),
        ]
    )

    assert User.objects.filter(email="person@example.org").count() == 2


@pytest.mark.django_db
def test_import_skips_an_account_that_a_user_holds():
    user = UserFactory(email="person@example.org", oidc_id="keycloak-id")

    output = run_import([keycloak_user()])

    assert User.objects.filter(oidc_id="keycloak-id").get() == user
    assert output.splitlines() == ["Created 0 user(s)."]


@pytest.mark.django_db
def test_import_creates_a_user_for_an_account_that_a_contact_holds():
    """A subject becomes a user, the contact keeps its access records until a migration."""
    contact = ContactFactory(email="person@example.org", oidc_id="keycloak-id")

    output = run_import([keycloak_user()])

    assert User.objects.filter(oidc_id="keycloak-id").exists()
    contact.refresh_from_db()
    assert contact.oidc_id == "keycloak-id"
    assert output.splitlines() == [
        f"Contact {contact.pk} has this id or email, it needs a migration: "
        "person@example.org (keycloak-id)",
        "Created 1 user(s).",
    ]


@pytest.mark.django_db
def test_import_creates_a_second_user_and_never_updates_the_stored_one():
    user = UserFactory(
        email="person@example.org",
        oidc_id=None,
        first_name="Stored",
        last_name="Name",
    )

    output = run_import([keycloak_user()])

    user.refresh_from_db()
    assert user.oidc_id is None
    assert user.first_name == "Stored"
    created = User.objects.get(oidc_id="keycloak-id")
    assert created.pk != user.pk
    assert output.splitlines() == [
        f"DAISY user {user.pk} has this email and no oidc_id, a second user: "
        "person@example.org (keycloak-id)",
        "Created 1 user(s).",
    ]


@pytest.mark.django_db
def test_import_creates_a_new_user_when_the_stored_one_is_inactive():
    """An inactive user is never adopted, and never activated by a job."""
    inactive = UserFactory(email="person@example.org", oidc_id=None, is_active=False)

    run_import([keycloak_user()])

    inactive.refresh_from_db()
    assert inactive.oidc_id is None
    assert not inactive.is_active
    created = User.objects.get(oidc_id="keycloak-id")
    assert created.pk != inactive.pk
    assert created.is_active


@pytest.mark.django_db
def test_import_creates_a_user_although_a_contact_has_the_email():
    """A contact is a record, not an identity: it is reported, not a reason to skip."""
    contact = ContactFactory(email="person@example.org", oidc_id=None)

    output = run_import([keycloak_user()])

    assert User.objects.filter(oidc_id="keycloak-id").exists()
    assert output.splitlines() == [
        f"Contact {contact.pk} has this id or email, it needs a migration: "
        "person@example.org (keycloak-id)",
        "Created 1 user(s).",
    ]


@pytest.mark.django_db
def test_import_skips_a_disabled_account():
    output = run_import([keycloak_user(enabled=False)])

    assert not User.objects.filter(oidc_id="keycloak-id").exists()
    assert output.splitlines() == [
        "Disabled in Keycloak, not created: 1 account(s).",
        "Created 0 user(s).",
    ]


@pytest.mark.django_db
def test_import_skips_an_account_without_an_email():
    output = run_import([keycloak_user(email=None)])

    assert not User.objects.filter(oidc_id="keycloak-id").exists()
    assert output.splitlines() == [
        "Without an email, not created: 1 account(s).",
        "Created 0 user(s).",
    ]


@pytest.mark.django_db
def test_import_reports_an_account_whose_username_an_older_row_holds():
    """The username is unique, and one account that DAISY cannot create stops nothing else."""
    UserFactory(username="person.example|ul", email="other@example.org", oidc_id=None)

    output = run_import(
        [
            keycloak_user(),
            keycloak_user(
                "other-id", email="second@example.org", username="second.person|ul"
            ),
        ]
    )

    assert not User.objects.filter(oidc_id="keycloak-id").exists()
    assert User.objects.filter(oidc_id="other-id").exists()
    assert "Not created: person@example.org (keycloak-id)" in output
    assert "Created 1 user(s)." in output


@pytest.mark.django_db
def test_import_dry_run_creates_nothing():
    output = run_import([keycloak_user()], "--dry-run")

    assert not User.objects.filter(oidc_id="keycloak-id").exists()
    assert output.splitlines() == ["Would create 1 user(s)."]
