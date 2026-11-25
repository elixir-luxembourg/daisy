import pytest
from django.shortcuts import reverse
from django.test.client import Client

from core.constants import Permissions
from test.factories import (
    AccessFactory,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
    ContactFactory,
    UserFactory,
)
from .utils import check_response_status, check_datasteward_restricted_url


def check_contact_view_permissions(url, user, action, contact):
    if action == Permissions.DELETE:
        # Only data stewards can delete a Contact instance
        if user.is_part_of(DataStewardGroup()):
            assert user.has_permission_on_object(
                f"core.{action.value}_contact", contact
            )
        else:
            assert not user.has_permission_on_object(
                f"core.{action.value}_contact", contact
            )

        check_response_status(url, user, [f"core.{action.value}_contact"], obj=contact)

    elif action is None:
        # Anyone can view or create a new Contact (no associated permission)
        check_response_status(url, user, [])

    elif action == Permissions.EDIT:
        # Anyone can edit a Contact instance
        check_response_status(url, user, [], obj=contact)

    else:
        # If other Permissions are needed, add the expected behavior
        raise ValueError(
            f"Unexpected permission {action} asked to work on Cohort instance"
        )


@pytest.mark.parametrize("group", [DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    "url_name, perm",
    [
        ("contacts", None),
        ("contact_edit", Permissions.EDIT),
        ("contact_add", None),
        ("contact_delete", Permissions.DELETE),
    ],
)
def test_contacts_views_permissions(permissions, group, url_name, perm):
    """
    Tests whether users from different groups can access the urls associated with Contact instances
    """
    contact = None
    if url_name in ["contacts", "contact_add", "contacts_export"]:
        url = reverse(url_name)
    else:
        contact = ContactFactory()
        contact.save()
        url = reverse(url_name, kwargs={"pk": contact.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_contact_view_permissions(url, user, perm, contact)


@pytest.mark.parametrize("group", [DataStewardGroup, LegalGroup, AuditorGroup])
def test_contacts_exports(permissions, group):
    url = reverse("contacts_export")
    user = UserFactory(groups=[group()])

    check_datasteward_restricted_url(url, user)


@pytest.mark.django_db
def test_manage_contacts_is_superuser_only(client):
    client.force_login(UserFactory())

    assert client.get(reverse("contacts_manage")).status_code == 403


@pytest.mark.django_db
def test_manage_contacts_shows_only_the_contacts_that_hold_a_subject(client):
    bound = ContactFactory(email="bound@example.org", oidc_id="subject-1")
    ContactFactory(email="plain@example.org", oidc_id=None)
    client.force_login(UserFactory(is_superuser=True))

    contacts = client.get(reverse("contacts_manage")).context["contacts"]

    assert [contact.pk for contact in contacts] == [bound.pk]


@pytest.mark.django_db
def test_manage_contacts_resolves_the_user_and_the_access_rows_of_a_contact(client):
    contact = ContactFactory(email="grantee@example.org", oidc_id="subject-1")
    user = UserFactory(oidc_id="subject-1")
    AccessFactory(contact=contact, user=None)
    client.force_login(UserFactory(is_superuser=True))

    response = client.get(reverse("contacts_manage"))
    row = response.context["contacts"][0]

    assert row.user_of_subject == user
    assert row.access_count == 1
    assert f"?contact__id__exact={contact.id}" in response.content.decode()


@pytest.mark.django_db
def test_manage_contacts_reports_a_contact_that_no_user_holds(client):
    ContactFactory(email="orphan@example.org", oidc_id="subject-1")
    client.force_login(UserFactory(is_superuser=True))

    row = client.get(reverse("contacts_manage")).context["contacts"][0]

    assert row.user_of_subject is None
    assert row.access_count == 0
