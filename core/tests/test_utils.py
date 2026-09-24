"""
records_with_email decides every email binding: the OIDC login, bind_or_create_user, get_contact
and BaseImporter.find_user.
"""

import pytest

from core.models import Contact, User
from core.utils import normalized_email, records_with_email
from test.factories import ContactFactory, UserFactory


@pytest.mark.django_db
def test_returns_the_record_of_the_email():
    user = UserFactory(email="person@example.org")

    assert records_with_email(User.objects.all(), "person@example.org") == [user]


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["PERSON@EXAMPLE.ORG", " person@example.org "])
def test_the_compared_email_is_the_normalized_one(email):
    """User.save() lower-cases the stored email, Keycloak and an import file send anything."""
    user = UserFactory(email="person@example.org")

    assert records_with_email(User.objects.all(), email) == [user]


@pytest.mark.django_db
@pytest.mark.parametrize("look_alike", ["admın@uni.lu", "ſmith@uni.lu"])
def test_a_look_alike_email_is_not_a_match(look_alike):
    """UPPER() folds `ı` to `I` and `ſ` to `S`, the prefilter alone would match."""
    UserFactory(username="admin", email="admin@uni.lu")
    UserFactory(username="smith", email="smith@uni.lu")

    assert records_with_email(User.objects.all(), look_alike) == []


@pytest.mark.django_db
def test_a_look_alike_email_keeps_its_own_record():
    """The two addresses are two people, each one finds itself and nobody else."""
    victim = UserFactory(username="victim", email="admin@uni.lu")
    look_alike = UserFactory(username="look-alike", email="admın@uni.lu")

    assert records_with_email(User.objects.all(), "admin@uni.lu") == [victim]
    assert records_with_email(User.objects.all(), "admın@uni.lu") == [look_alike]


@pytest.mark.django_db
def test_every_record_of_one_email_comes_back():
    """Two records on one email is what the callers refuse to bind, so they need both."""
    first = UserFactory(username="first", email="person@example.org")
    second = UserFactory(username="second", email="person@example.org")

    found = records_with_email(User.objects.all(), "person@example.org")

    assert sorted(user.pk for user in found) == sorted([first.pk, second.pk])


@pytest.mark.django_db
def test_the_queryset_keeps_its_own_filters():
    UserFactory(username="inactive", email="person@example.org", is_active=False)
    active = UserFactory(username="active", email="person@example.org")

    found = records_with_email(
        User.objects.filter(is_active=True), "person@example.org"
    )

    assert found == [active]


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["", None, "   "])
def test_no_email_matches_nothing(email):
    UserFactory(email="person@example.org")

    assert records_with_email(User.objects.all(), email) == []


@pytest.mark.django_db
def test_it_works_on_any_model_with_an_email():
    """get_contact() passes contacts, the callers pass users."""
    contact = ContactFactory(email="person@example.org")

    assert records_with_email(Contact.objects.all(), "person@example.org") == [contact]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("  Person@Example.ORG ", "person@example.org"), (None, ""), ("", "")],
)
def test_normalized_email(raw, expected):
    assert normalized_email(raw) == expected
