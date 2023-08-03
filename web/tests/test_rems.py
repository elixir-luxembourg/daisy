import json

from core.models import Access
from core.utils import DaisyLogger

from django.shortcuts import reverse

import datetime

from test.factories import UserFactory, DatasetFactory, AccessFactory

log = DaisyLogger(__name__)

def test_rems_handler_duplicate(client, user_vip, user_data_steward):
    resource_id = "TEST-2-5591E3-1"
    expiration_date = datetime.date.today() + datetime.timedelta(days=1)
    email = "john.doe@uni.lu"
    user = UserFactory(oidc_id='12345', email=email)
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    application_id = 4056
    data = [{"application": application_id, "resource": resource_id, "user": user.oidc_id,
            "mail": email, "end": expiration_date.strftime('%Y-%m-%d') + "T23:59:59.000Z"}]

    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200 , response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1

def test_rems_handler_no_expiration(client, user_vip, user_data_steward):
    resource_id = "TEST-2-5591E3-1"
    email = "john.doe@uni.lu"
    user = UserFactory(oidc_id='12345', email=email)
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    application_id = 4056
    data = [{"application": application_id, "resource": resource_id, "user": user.oidc_id,
             "mail": email, "end": None}]

    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1

def test_rems_handler_different_expiration(client, user_vip, user_data_steward):
    resource_id = "TEST-2-5591E3-1"
    expiration_date_1 = datetime.date.today() + datetime.timedelta(days=1)
    expiration_date_2 = datetime.date.today() + datetime.timedelta(days=2)
    email = "john.doe@uni.lu"
    user = UserFactory(oidc_id='12345', email=email)
    user.save()
    dataset = DatasetFactory(title='Test', local_custodians=[user], elu_accession=resource_id)
    dataset.save()
    application_id = 4056
    data = [{"application": application_id, "resource": resource_id, "user": user.oidc_id,
             "mail": email, "end": expiration_date_1.strftime('%Y-%m-%d') + "T23:59:59.000Z"}]

    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 1
    data[0]['end'] = expiration_date_2.strftime('%Y-%m-%d') + "T23:59:59.000Z"
    response = client.post(reverse('api_rems_endpoint'), json.dumps(data), content_type="application/json")
    assert response.status_code == 200, response.content
    accesses = Access.objects.filter(dataset=dataset, user=user).all()
    assert len(accesses) == 2
