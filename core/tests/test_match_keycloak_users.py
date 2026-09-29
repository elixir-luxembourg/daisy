from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from core.constants import IdentityProvider
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


def run_match(keycloak_users, *args):
    with patch(
        "core.management.commands.match_keycloak_users.KeycloakBackend"
    ) as backend:
        backend.return_value.get_list_of_users.return_value = keycloak_users
        output = StringIO()
        call_command("match_keycloak_users", *args, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
def test_match_binds_an_unbound_user_by_case_insensitive_email():
    user = UserFactory(email="PERSON@EXAMPLE.ORG", oidc_id=None)

    output = run_match([keycloak_user()])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"
    assert output.splitlines() == ["Bound 1 user(s) to a Keycloak account."]


@pytest.mark.django_db
def test_match_binds_any_identity_provider():
    user = UserFactory(email="person@example.org", oidc_id=None)

    run_match([keycloak_user(identity_provider=IdentityProvider.ORCID)])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"


@pytest.mark.django_db
def test_match_binds_an_inactive_user():
    """The match writes the oidc_id only, a login decides whether the person gets in."""
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=False)

    run_match([keycloak_user()])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"
    assert not user.is_active


@pytest.mark.django_db
def test_match_never_deactivates_a_user_that_keycloak_does_not_know():
    user = UserFactory(email="person@example.org", oidc_id=None, is_active=True)

    output = run_match([])

    user.refresh_from_db()
    assert user.is_active
    assert user.oidc_id is None
    assert output.splitlines() == [
        "No Keycloak account: person@example.org",
        "Bound 0 user(s) to a Keycloak account.",
    ]


@pytest.mark.django_db
def test_match_leaves_a_bound_user_alone():
    user = UserFactory(email="person@example.org", oidc_id="stored-id")

    output = run_match([keycloak_user("another-id")])

    user.refresh_from_db()
    assert user.oidc_id == "stored-id"
    assert output.splitlines() == ["Bound 0 user(s) to a Keycloak account."]


@pytest.mark.django_db
def test_match_reports_several_keycloak_accounts_for_one_email():
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_match([keycloak_user("first-id"), keycloak_user("second-id")])

    user.refresh_from_db()
    assert user.oidc_id is None
    assert output.splitlines() == [
        f"Several Keycloak accounts, not bound: person@example.org (DAISY user {user.pk})",
        "  first-id  University of Luxembourg",
        "  second-id  University of Luxembourg",
        "Bound 0 user(s) to a Keycloak account.",
    ]


@pytest.mark.django_db
def test_match_reports_several_daisy_users_for_one_email():
    first_user = UserFactory(email="person@example.org", oidc_id=None)
    second_user = UserFactory(email="PERSON@EXAMPLE.ORG", oidc_id=None)

    output = run_match([keycloak_user()])

    first_user.refresh_from_db()
    second_user.refresh_from_db()
    assert first_user.oidc_id is None
    assert second_user.oidc_id is None
    users_list = ", ".join(str(pk) for pk in sorted([first_user.pk, second_user.pk]))
    assert (
        f"Several DAISY users, not bound: person@example.org (DAISY users {users_list})"
        in output.splitlines()
    )


@pytest.mark.django_db
def test_match_reports_an_account_that_another_user_holds():
    owner = UserFactory(email="owner@example.org", oidc_id="keycloak-id")
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_match([keycloak_user()])

    user.refresh_from_db()
    owner.refresh_from_db()
    assert user.oidc_id is None
    assert owner.oidc_id == "keycloak-id"
    assert output.splitlines() == [
        "Keycloak account keycloak-id already belongs to another DAISY record, "
        f"not bound: person@example.org (DAISY user {user.pk})",
        "Bound 0 user(s) to a Keycloak account.",
    ]


@pytest.mark.django_db
def test_match_binds_an_account_that_a_contact_holds():
    """A contact is a record, not an identity: only a user makes an account taken."""
    contact = ContactFactory(email="contact@example.org", oidc_id="keycloak-id")
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_match([keycloak_user()])

    user.refresh_from_db()
    assert user.oidc_id == "keycloak-id"
    contact.refresh_from_db()
    assert contact.oidc_id == "keycloak-id"
    assert output.splitlines() == ["Bound 1 user(s) to a Keycloak account."]


@pytest.mark.django_db
def test_match_binds_the_other_users_when_one_email_is_ambiguous():
    shared = UserFactory(email="shared@example.org", oidc_id=None)
    single = UserFactory(email="single@example.org", oidc_id=None)

    run_match(
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
def test_match_ignores_a_keycloak_account_without_an_email():
    user = UserFactory(email="person@example.org", oidc_id=None)

    output = run_match([keycloak_user(email=None)])

    user.refresh_from_db()
    assert user.oidc_id is None
    assert "No Keycloak account: person@example.org" in output.splitlines()


@pytest.mark.django_db
def test_match_dry_run_reports_without_writing():
    user = UserFactory(email="person@example.org", oidc_id=None)
    unmatched = UserFactory(email="nobody@example.org", oidc_id=None)

    output = run_match([keycloak_user()], "--dry-run")

    user.refresh_from_db()
    assert user.oidc_id is None
    assert output.splitlines() == [
        f"No Keycloak account: {unmatched.email}",
        "Would bind 1 user(s) to a Keycloak account.",
    ]
