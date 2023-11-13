import datetime
import json

from django.shortcuts import reverse
from faker import Faker

from core.models import Access
from core.models import Contact
from core.synchronizers import ExternalUserNotFoundException
from core.utils import DaisyLogger
from test.factories import UserFactory, DatasetFactory, ContactFactory

log = DaisyLogger(__name__)


def patch_get_external_user_info(
    mocker,
    expected_oidc_id="12345",
    first_name="John",
    last_name="Doe",
    email="john.doe@test.com",
):
    def mock_get_external_user_info(self, oidc_id):
        if oidc_id == expected_oidc_id:
            return {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "id": expected_oidc_id,
            }
        else:
            raise ExternalUserNotFoundException()

    mocker.patch(
        "core.synchronizers.DummySynchronizationBackend.get_external_user_info",
        mock_get_external_user_info,
    )


def test_rems_handler_user_by_oidc_updated(client, user_vip, user_data_steward, mocker):
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
    user.refresh_from_db()
    assert user.first_name == "Jane"
    assert user.last_name == "Davis"
    assert user.email == "jane.davis@test.com"


def test_rems_handler_duplicate(client, user_vip, user_data_steward, mocker):
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


def test_rems_handler_no_expiration(client, user_vip, user_data_steward, mocker):
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


def test_rems_handler_different_expiration(client, user_vip, user_data_steward, mocker):
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


def test_rems_handler_user_not_found(client, user_vip, user_data_steward, mocker):
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


def test_rems_handler_contact_by_oidc_updated(
    client, user_vip, user_data_steward, mocker
):
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker, first_name="Jane", last_name="Davis", email="jane.davis@test.com"
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    contact = ContactFactory(oidc_id="12345", email=email)
    contact.save()
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
    accesses = Access.objects.filter(dataset=dataset, contact=contact).all()
    contact.refresh_from_db()
    assert len(accesses) == 1
    assert contact.first_name == "Jane"
    assert contact.last_name == "Davis"
    assert contact.email == "jane.davis@test.com"


def test_rems_handler_user_by_email_updated(
    client, user_vip, user_data_steward, mocker
):
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
    user.refresh_from_db()
    assert user.first_name == "Jane"
    assert user.last_name == "Davis"
    assert user.email == email


def test_rems_handler_user_by_email_multiple(
    client, user_vip, user_data_steward, mocker
):
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker, first_name="Jane", last_name="Davis", email=email
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
    assert response.status_code == 500, response.content
    assert response.json()["status"] == "Failure"
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 0
    user.refresh_from_db()
    assert user.first_name == user_original_first_name
    assert user.last_name == user_original_last_name
    assert user.email == email


def test_rems_handler_contact_by_email_updated(
    client, user_vip, user_data_steward, mocker
):
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker, first_name="Jane", last_name="Davis", email=email
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    contact = ContactFactory(oidc_id=None, email=email)
    contact.save()
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
    accesses = Access.objects.filter(dataset=dataset, contact=contact).all()
    assert len(accesses) == 1
    contact.refresh_from_db()
    assert contact.first_name == "Jane"
    assert contact.last_name == "Davis"
    assert contact.email == email


def test_rems_handler_contact_by_email_multiple(
    client, user_vip, user_data_steward, mocker
):
    email = "john.doe@test.com"
    patch_get_external_user_info(
        mocker, first_name="Jane", last_name="Davis", email=email
    )
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    contact = ContactFactory(oidc_id=None, email=email)
    contact.save()
    contact_original_first_name = contact.first_name
    contact_original_last_name = contact.last_name
    faker = Faker()
    contact2 = Contact(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=email,
    )
    contact2.type = contact.type
    contact2.save()
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
    assert response.status_code == 500, response.content
    assert response.json()["status"] == "Failure"
    accesses = Access.objects.filter(dataset=dataset).all()
    assert len(accesses) == 0
    contact.refresh_from_db()
    assert contact.first_name == contact_original_first_name
    assert contact.last_name == contact_original_last_name
    assert contact.email == email


def test_rems_handler_contact_created(client, user_vip, user_data_steward, mocker):
    faker = Faker()
    email = faker.email()
    first_name = faker.first_name()
    last_name = faker.last_name()
    patch_get_external_user_info(
        mocker, first_name=first_name, last_name=last_name, email=email
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
    contact = accesses[0].contact
    assert contact.first_name == first_name
    assert contact.last_name == last_name
    assert contact.email == email
    assert contact.oidc_id == "12345"
    assert contact.type.name == "Other"
