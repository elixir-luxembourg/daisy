from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from core.constants import IdentityProvider
from core.synchronizers import OIDCUser
from test.factories import UserFactory


def keycloak_user(
    oidc_id="keycloak-id",
    email="person@example.org",
    username="person.example",
    identity_provider=IdentityProvider.UL,
):
    return OIDCUser(
        id=oidc_id,
        email=email,
        first_name="Person",
        last_name="Example",
        username=username,
        identity_provider=identity_provider,
    )


def run_sync(keycloak_users, *args):
    with patch(
        "core.management.commands.sync_keycloak_users.KeycloakBackend"
    ) as backend:
        backend.return_value.get_list_of_users.return_value = keycloak_users
        output = StringIO()
        call_command("sync_keycloak_users", *args, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
def test_sync_assigns_oidc_id_to_unbound_user_by_case_insensitive_email():
    user = UserFactory(email="PERSON@EXAMPLE.ORG", oidc_id=None)

    output = run_sync([keycloak_user()])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"
    assert output.splitlines() == [
        "Updated 1 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_deactivates_active_non_superuser_missing_from_keycloak():
    user = UserFactory(oidc_id="missing-id", is_active=True)

    output = run_sync([])

    user.refresh_from_db()
    assert not user.is_active
    assert output.splitlines() == [
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 1 user(s).",
    ]


@pytest.mark.django_db
def test_sync_keeps_unmatched_user_active_without_flag():
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=True)

    output = run_sync([])

    user.refresh_from_db()
    assert user.is_active
    assert output.splitlines() == [
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_deactivates_unmatched_user_with_flag():
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=True)

    output = run_sync([], "--deactivate-unmatched")

    user.refresh_from_db()
    assert not user.is_active
    assert output.splitlines() == [
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 1 user(s).",
    ]


@pytest.mark.django_db
def test_sync_flag_does_not_deactivate_unmatched_superuser():
    user = UserFactory(
        email="person@example.org",
        oidc_id=None,
        is_active=True,
        is_superuser=True,
    )

    run_sync([], "--deactivate-unmatched")

    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db
def test_sync_preserves_inactive_superuser_and_keycloak_matched_users():
    inactive_user = UserFactory(oidc_id="inactive-id", is_active=False)
    superuser = UserFactory(oidc_id="superuser-id", is_superuser=True)
    matched_user = UserFactory(oidc_id="matched-id")

    output = run_sync([keycloak_user("matched-id", matched_user.email)])

    inactive_user.refresh_from_db()
    superuser.refresh_from_db()
    matched_user.refresh_from_db()
    assert not inactive_user.is_active
    assert superuser.is_active
    assert matched_user.is_active
    assert output.splitlines() == [
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_dry_run_reports_without_updating_or_deactivating():
    unbound_user = UserFactory(email="person@example.org", oidc_id=None)
    missing_user = UserFactory(oidc_id="missing-id", is_active=True)

    output = run_sync([keycloak_user()], "--dry-run")

    unbound_user.refresh_from_db()
    missing_user.refresh_from_db()
    assert unbound_user.oidc_id is None
    assert missing_user.is_active
    assert output.splitlines() == [
        "Would update 1 user(s) with an oidc_id.",
        "Would deactivate 1 user(s).",
        f"No Keycloak account: {missing_user.email}",
    ]


@pytest.mark.django_db
def test_sync_dry_run_lists_an_unmatched_user_without_the_flag():
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_sync([], "--dry-run")

    user.refresh_from_db()
    assert user.is_active
    assert output.splitlines() == [
        "Would update 0 user(s) with an oidc_id.",
        "Would deactivate 0 user(s).",
        "No Keycloak account: person@example.org",
    ]


@pytest.mark.django_db
def test_sync_ignores_keycloak_account_without_email():
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_sync([keycloak_user(email=None)])

    user.refresh_from_db()
    assert user.oidc_id is None
    assert output.splitlines() == [
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_reports_a_shared_keycloak_email_and_binds_nothing_for_it():
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_sync(
        [
            keycloak_user("first-id"),
            keycloak_user("second-id"),
        ]
    )

    user.refresh_from_db()
    assert user.oidc_id is None
    assert output.splitlines() == [
        f"Shared email, not bound: person@example.org (DAISY user {user.pk})",
        "  first-id  University of Luxembourg",
        "  second-id  University of Luxembourg",
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_keeps_a_user_with_a_shared_keycloak_email_active():
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=True)

    output = run_sync(
        [keycloak_user("first-id"), keycloak_user("second-id")],
        "--deactivate-unmatched",
    )

    user.refresh_from_db()
    assert user.is_active
    assert "Deactivated 0 user(s)." in output


@pytest.mark.django_db
def test_sync_binds_the_other_users_when_one_email_is_shared():
    shared = UserFactory(email="shared@example.org", oidc_id=None)
    single = UserFactory(email="single@example.org", oidc_id=None)

    run_sync(
        [
            keycloak_user("first-id", email="shared@example.org"),
            keycloak_user("second-id", email="shared@example.org"),
            keycloak_user("single-id", email="single@example.org"),
        ]
    )

    shared.refresh_from_db()
    single.refresh_from_db()
    assert shared.oidc_id is None
    assert single.oidc_id == "single-id"


@pytest.mark.django_db
def test_sync_dry_run_lists_an_inactive_unbound_user():
    UserFactory(email="person@example.org", oidc_id=None, is_active=False)

    output = run_sync([], "--dry-run")

    assert "No Keycloak account: person@example.org" in output.splitlines()


@pytest.mark.django_db
def test_sync_rejects_multiple_daisy_users_for_one_keycloak_identity():
    first_user = UserFactory(email="person@example.org", oidc_id=None)
    second_user = UserFactory(email="PERSON@EXAMPLE.ORG", oidc_id=None)

    with pytest.raises(CommandError, match="multiple DAISY users"):
        run_sync([keycloak_user()])

    first_user.refresh_from_db()
    second_user.refresh_from_db()
    assert first_user.oidc_id is None
    assert second_user.oidc_id is None


@pytest.mark.django_db
def test_sync_rejects_keycloak_identity_already_owned_by_another_user():
    owner = UserFactory(oidc_id="keycloak-id")
    unbound_user = UserFactory(email="person@example.org", oidc_id=None)

    with pytest.raises(
        CommandError, match=f"already assigned to DAISY user {owner.pk}"
    ):
        run_sync([keycloak_user()])

    unbound_user.refresh_from_db()
    assert unbound_user.oidc_id is None


@pytest.mark.django_db
def test_sync_does_not_bind_an_account_of_another_identity_provider():
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=True)

    output = run_sync(
        [keycloak_user(identity_provider=IdentityProvider.ORCID)],
        "--deactivate-unmatched",
    )

    user.refresh_from_db()
    assert user.oidc_id is None
    # Keycloak knows them, so they are not reported as missing and stay active
    assert user.is_active
    assert output.splitlines() == [
        "Identity provider not allowed, not bound: person@example.org (ORCID)",
        "Updated 0 user(s) with an oidc_id.",
        "Deactivated 0 user(s).",
    ]


@pytest.mark.django_db
def test_sync_binds_the_allowed_account_when_the_email_has_several_providers():
    user = UserFactory(email="person@example.org", oidc_id=None)

    run_sync(
        [
            keycloak_user("orcid-id", identity_provider=IdentityProvider.ORCID),
            keycloak_user("ul-id", identity_provider=IdentityProvider.UL),
        ]
    )

    user.refresh_from_db()
    assert user.oidc_id == "ul-id"


@pytest.mark.django_db
@override_settings(OIDC_ALLOWED_IDENTITY_PROVIDERS=[])
def test_sync_binds_any_provider_when_none_is_configured():
    user = UserFactory(email="person@example.org", oidc_id=None)

    run_sync([keycloak_user(identity_provider=IdentityProvider.ORCID)])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"
