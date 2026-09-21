import datetime
import json

from django.shortcuts import reverse
from faker import Faker

from core.models import Access
from core.models import Contact, User
from core.synchronizers import ExternalUserNotFoundException, OIDCUser
from core.utils import DaisyLogger
from test.factories import UserFactory, DatasetFactory, ContactFactory

log = DaisyLogger(__name__)


def patch_get_external_user_info(
    mocker,
    expected_oidc_id="12345",
    first_name="John",
    last_name="Doe",
    email="john.doe@test.com",
    username=None,
):
    def mock_get_external_user_info(self, oidc_id):
        if oidc_id == expected_oidc_id:
            return OIDCUser(
                id=expected_oidc_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                username=username or email,
            )
        else:
            raise ExternalUserNotFoundException()

    mocker.patch(
        "core.synchronizers.DummySynchronizationBackend.get_external_user_info",
        mock_get_external_user_info,
    )


def test_rems_handler_user_by_oidc_is_never_updated(
    client, user_custodian, user_data_steward, mocker
):
    """The subject names the user, and nothing updates a stored row."""
    email = "john.doe@uni.lu"
    patch_get_external_user_info(
        mocker,
        first_name="Jane",
        last_name="Davis",
        email="jane.davis@test.com",
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": user.oidc_id,
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    stored_first_name, stored_last_name = user.first_name, user.last_name
    user.refresh_from_db()
    assert user.first_name == stored_first_name
    assert user.last_name == stored_last_name
    assert user.email == email


def test_rems_handler_activates_an_inactive_user_of_the_subject(
    client, user_custodian, user_data_steward, mocker
):
    """The same rule as the login, see test_oidc_login."""
    email = "john.doe@uni.lu"
    patch_get_external_user_info(mocker, email=email)
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id="12345", email=email, is_active=False)
    dataset = DatasetFactory(
        title="Test", local_custodians=[user_data_steward], elu_accession=resource_id
    )
    data = [
        {
            "application": 4057,
            "resource": resource_id,
            "user": user.oidc_id,
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 200, response.content
    user.refresh_from_db()
    assert user.is_active
    assert User.objects.filter(oidc_id="12345").count() == 1
    assert Access.objects.filter(dataset=dataset, user=user).count() == 1


def test_rems_handler_duplicate(client, user_custodian, user_data_steward, mocker):
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, email=email)
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": user.oidc_id,
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1


def test_rems_handler_no_expiration(client, user_custodian, user_data_steward, mocker):
    resource_id = "TEST-2-5591E3-1"
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, email=email)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": user.oidc_id,
            "mail": email,
            "end": None,
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1


def test_rems_handler_different_expiration(
    client, user_custodian, user_data_steward, mocker
):
    resource_id = "TEST-2-5591E3-1"
    expiration_date_1 = datetime.date.today() + datetime.timedelta(days=1)
    expiration_date_2 = datetime.date.today() + datetime.timedelta(days=2)
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, email=email)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": user.oidc_id,
            "mail": email,
            "end": expiration_date_1.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    data[0]["end"] = expiration_date_2.strftime("%Y-%m-%d") + "T23:59:59.000Z"
    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 2


def test_rems_handler_user_not_found(client, user_custodian, user_data_steward, mocker):
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, expected_oidc_id="not_found")
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": "not found",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 500, response.content
    assert response.json()["status"] == "Failure"
    accesses = Access.objects.filter(dataset=dataset).all()
    assert len(accesses) == 0


def test_rems_handler_creates_a_user_for_a_subject_that_a_contact_holds(
    client, user_custodian, user_data_steward, mocker
):
    """A subject becomes a user, the contact keeps its access records until a migration."""
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, email=email, username="john.doe|ul")
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    contact = ContactFactory(oidc_id="12345", email=email)
    contact.save()
    dataset = DatasetFactory(title="Test", elu_accession=resource_id)
    dataset.save()
    data = [
        {
            "application": 4056,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    created = User.objects.get(oidc_id="12345")
    assert created.username == "john.doe|ul"
    assert [access.user for access in Access.objects.filter(dataset=dataset)] == [
        created
    ]
    contact.refresh_from_db()
    assert contact.oidc_id == "12345"


def test_rems_handler_binds_an_unbound_user_of_that_email(
    client, user_custodian, user_data_steward, mocker
):
    """One active user waits unbound for that email: the entitlement binds it, nothing else."""
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker, first_name="Jane", last_name="Davis", email=email
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id=None, email=email)
    user.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    stored_first_name = user.first_name
    user.refresh_from_db()
    assert user.oidc_id == "12345"
    assert user.first_name == stored_first_name
    assert user.email == email
    assert User.objects.filter(email=email).count() == 1


def test_rems_handler_creates_a_user_when_the_email_is_ambiguous(
    client, user_custodian, user_data_steward, mocker
):
    """
    Nothing says which of the two rows is the person, so the subject gets a user of its own and
    the entitlement is granted: a person must not lose an access over a DAISY duplicate.
    """
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker,
        first_name="Jane",
        last_name="Davis",
        email=email,
        username="jane.davis|ul",
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id=None, email=email)
    user.save()
    user_original_first_name = user.first_name
    user_original_last_name = user.last_name
    user2 = UserFactory(oidc_id=None, email=email)
    user2.save()
    dataset = DatasetFactory(
        title="Test", local_custodians=[user], elu_accession=resource_id
    )
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    created = User.objects.get(oidc_id="12345")
    assert created.username == "jane.davis|ul"
    assert created.is_active
    assert not created.has_usable_password()
    assert [access.user for access in Access.objects.filter(dataset=dataset)] == [
        created
    ]
    # the two stored rows are left alone, a data steward sorts them out
    user.refresh_from_db()
    assert user.oidc_id is None
    assert user.first_name == user_original_first_name
    assert user.last_name == user_original_last_name
    assert user.email == email


def test_rems_handler_ignores_a_contact_with_the_same_email(
    client, user_custodian, user_data_steward, mocker
):
    """
    A contact is a record, not an identity: the subject gets a user, and the contact of that
    email is left untouched. Two such contacts do not block the entitlement either.
    """
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker,
        first_name="Jane",
        last_name="Davis",
        email=email,
        username="jane.davis|ul",
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    contact = ContactFactory(oidc_id=None, email=email)
    contact.save()
    contact_original_first_name = contact.first_name
    faker = Faker()
    namesake = Contact(
        first_name=faker.first_name(), last_name=faker.last_name(), email=email
    )
    namesake.type = contact.type
    namesake.save()
    dataset = DatasetFactory(title="Test", elu_accession=resource_id)
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    created = User.objects.get(oidc_id="12345")
    assert created.username == "jane.davis|ul"
    assert [access.user for access in Access.objects.filter(dataset=dataset)] == [
        created
    ]
    assert not Access.objects.filter(contact__isnull=False).exists()
    contact.refresh_from_db()
    assert contact.oidc_id is None
    assert contact.first_name == contact_original_first_name


def test_rems_handler_creates_a_user_for_an_unknown_subject(
    client, user_custodian, user_data_steward, mocker
):
    """Keycloak knows every REMS grantee, so a subject DAISY does not hold becomes a user."""
    faker = Faker()
    email = faker.email()
    first_name = faker.first_name()
    last_name = faker.last_name()
    patch_get_external_user_info(
        mocker,
        first_name=first_name,
        last_name=last_name,
        email=email,
        username="new.grantee|ul",
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    dataset = DatasetFactory(title="Test", elu_accession=resource_id)
    dataset.save()
    application_id = 4056
    data = [
        {
            "application": application_id,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset).all()
    assert len(accesses) == 1
    user = accesses[0].user
    assert accesses[0].contact is None
    assert user.username == "new.grantee|ul"
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.email == email
    assert user.oidc_id == "12345"
    assert user.is_active
    assert not user.has_usable_password()
    # no contact is created for a Keycloak account any more
    assert not Contact.objects.exists()


def test_rems_handler_uses_the_user_when_a_contact_holds_the_subject_too(
    client, user_custodian, user_data_steward, mocker
):
    """The user of the subject answers, the contact of the same subject is only reported."""
    email = "john.doe@test.com"
    patch_get_external_user_info(mocker, email=email)
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    user = UserFactory(oidc_id="12345", email=email)
    user.save()
    ContactFactory(oidc_id="12345", email=email).save()
    dataset = DatasetFactory(title="Test", elu_accession=resource_id)
    dataset.save()
    data = [
        {
            "application": 4056,
            "resource": resource_id,
            "user": "12345",
            "mail": email,
            "end": expiration_date.strftime("%Y-%m-%d") + "T23:59:59.000Z",
        }
    ]

    response = client.post(
        reverse("api_rems_endpoint"), json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200, response.content
    assert [access.user for access in Access.objects.filter(dataset=dataset)] == [user]
