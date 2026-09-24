"""
process_contacts resolves a contact of an import file: a DAISY user, else a Keycloak account
that becomes a user, else a contact.
"""

from unittest.mock import patch

import pytest
from django.test import override_settings

from core.constants import IdentityProvider
from core.importer.datasets_importer import DatasetsImporter
from core.models import Contact, User
from core.synchronizers import OIDCUser
from test.factories import (
    ContactFactory,
    ContactTypeFactory,
    PartnerFactory,
    UserFactory,
)


def contact_dict(role="Principal_Investigator", affiliations=None):
    return {
        "first_name": "Person",
        "last_name": "Example",
        "email": "person@example.org",
        "role": role,
        "affiliations": (
            affiliations if affiliations is not None else ["Example Partner"]
        ),
    }


def keycloak_account(oidc_id="keycloak-id", username="person.example|ul"):
    return OIDCUser(
        id=oidc_id,
        email="person@example.org",
        first_name="Person",
        last_name="Example",
        username=username,
        identity_provider=IdentityProvider.UL,
        enabled=True,
    )


@pytest.fixture
def importer():
    ContactTypeFactory(name="Other")
    ContactTypeFactory(name="Principal_Investigator")
    return DatasetsImporter(exit_on_error=True, verbose=False, validate=False)


def run(importer, accounts=None, contacts=None):
    """Keycloak answers with `accounts`, and without the integration it is never asked."""
    with patch(
        "core.importer.base_importer.KeycloakBackend"
    ) as backend, override_settings(KEYCLOAK_INTEGRATION=accounts is not None):
        backend.return_value.get_users_by_email.return_value = accounts or []
        return importer.process_contacts(contacts or [contact_dict()])


@pytest.mark.django_db
def test_an_active_user_is_reused(importer):
    user = UserFactory(first_name="Person", last_name="Example")

    custodians, personnel, contacts = run(importer)

    assert custodians == [user]
    assert (personnel, contacts) == ([], [])
    assert User.objects.filter(last_name="Example").count() == 1


@pytest.mark.django_db
def test_the_email_wins_over_the_name(importer):
    UserFactory(
        first_name="Person",
        last_name="Example",
        username="namesake",
        email="another@example.org",
    )
    wanted = UserFactory(
        first_name="Person",
        last_name="Example",
        username="person.example",
        email="person@example.org",
    )

    custodians, _, _ = run(importer)

    assert custodians == [wanted]


@pytest.mark.django_db
def test_an_inactive_user_is_never_reused(importer):
    """It is a leaver or a placeholder, and a login cannot activate a stored row."""
    inactive = UserFactory(
        first_name="Person",
        last_name="Example",
        username="person.example",
        is_active=False,
    )

    custodians, _, _ = run(importer, accounts=[keycloak_account()])

    created = User.objects.get(oidc_id="keycloak-id")
    assert custodians == [created]
    assert created.pk != inactive.pk
    # the username comes from Keycloak, the importer does not invent one
    assert created.username == "person.example|ul"
    assert not created.has_usable_password()


@pytest.mark.django_db
def test_a_keycloak_account_becomes_a_user(importer):
    custodians, _, contacts = run(importer, accounts=[keycloak_account()])

    created = User.objects.get(oidc_id="keycloak-id")
    assert custodians == [created]
    assert created.is_active
    assert contacts == []
    assert not Contact.objects.exists()


@pytest.mark.django_db
def test_every_keycloak_account_of_the_email_becomes_a_user(importer):
    accounts = [
        keycloak_account("ul-id", "person.example|ul"),
        keycloak_account("orcid-id", "person.example|orcid"),
    ]

    custodians, _, _ = run(importer, accounts=accounts)

    assert User.objects.filter(email="person@example.org").count() == 2
    # the first account of the response is the user of this contact
    assert custodians == [User.objects.get(oidc_id="ul-id")]


@pytest.mark.django_db
def test_a_bound_user_is_not_created_twice(importer):
    user = UserFactory(
        username="person.example|ul",
        email="person@example.org",
        oidc_id="keycloak-id",
        is_active=False,
    )

    custodians, _, _ = run(importer, accounts=[keycloak_account()])

    assert custodians == [user]
    assert User.objects.filter(oidc_id="keycloak-id").count() == 1


@pytest.mark.django_db
def test_a_person_without_a_keycloak_account_becomes_a_contact(importer):
    PartnerFactory(name="Example Partner")

    custodians, personnel, contacts = run(importer, accounts=[])

    assert (custodians, personnel) == ([], [])
    assert [contact.email for contact in contacts] == ["person@example.org"]
    assert not User.objects.filter(email="person@example.org").exists()


@pytest.mark.django_db
def test_an_existing_contact_is_reused(importer):
    partner = PartnerFactory(name="Example Partner")
    contact = ContactFactory(
        first_name="Person", last_name="Example", email="person@example.org"
    )
    contact.partners.add(partner)

    _, _, contacts = run(importer, accounts=[])

    assert contacts == [contact]
    assert Contact.objects.count() == 1


@pytest.mark.django_db
def test_a_contact_that_holds_the_account_does_not_stop_the_user(importer):
    """A subject becomes a user, the contact keeps its access records until a migration."""
    contact = ContactFactory(
        first_name="Person",
        last_name="Example",
        email="person@example.org",
        oidc_id="keycloak-id",
    )

    custodians, _, contacts = run(importer, accounts=[keycloak_account()])

    created = User.objects.get(oidc_id="keycloak-id")
    assert custodians == [created]
    assert contacts == []
    contact.refresh_from_db()
    assert contact.oidc_id == "keycloak-id"


@pytest.mark.django_db
def test_keycloak_is_not_asked_without_the_integration(importer):
    PartnerFactory(name="Example Partner")

    custodians, _, contacts = run(importer)

    assert custodians == []
    assert len(contacts) == 1


@pytest.mark.django_db
def test_the_role_decides_custodian_or_personnel(importer):
    user = UserFactory(first_name="Person", last_name="Example")

    custodians, personnel, _ = run(importer, contacts=[contact_dict(role="Researcher")])

    assert custodians == []
    assert personnel == [user]
