from json import loads

from importlib import reload

from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.urls import reverse
from django.test import RequestFactory

from web.views import api

from test.factories import UserFactory, EndpointFactory, DatasetFactory, ExposureFactory, ProjectFactory
from web.views.api import create_error_response, create_protect_with_api_key_decorator
from web.views.api import permissions


def test_create_error_response():
    assert type(create_error_response('test')) == JsonResponse
    assert create_error_response('test').status_code == 500
    assert create_error_response('test', status=501).status_code == 501    

    body = loads(create_error_response('description_value', {'more': 'information'}).content)
    assert body.get('description') == 'description_value'
    assert body.get('more') == 'information'

# def test_protect_with_api_key(override_global_api_key):  # see conftest.py
def test_protect_with_api_key():
    test_global_key = 'GLOBAL_API_KEY__as_set_in_tests'

    user = UserFactory.create(first_name='Rebecca', last_name='Kafe')
    user.save()
    user_key = user.api_key

    def dummy_view(request):
        return JsonResponse('Success', safe=False)

    protect_with_api_key = create_protect_with_api_key_decorator(test_global_key)

    @protect_with_api_key
    def dummy_protected_view(request):
        return JsonResponse('Success', safe=False)

    request = RequestFactory().get('')
    
    # Check if no error if a view is called without the decorator
    response = dummy_view(request)
    assert response.status_code == 200

    # check if error is returned when API_KEY is missing
    failed_response = dummy_protected_view(request)
    assert failed_response.status_code == 403

    # check if view is returned when GLOBAL_API_KEY is valid in GET
    request = RequestFactory().get('', data={'API_KEY': test_global_key})
    response = dummy_protected_view(request)
    assert response.status_code == 200

    # check if view is returned when GLOBAL_API_KEY is valid in POST
    request = RequestFactory().post('', data={'API_KEY': test_global_key})
    response = dummy_protected_view(request)
    assert response.status_code == 200

    # check if view is returned when User's API KEY is valid in GET
    request = RequestFactory().get('', data={'API_KEY': user_key})
    request.user = user
    assert response.status_code == 200

    # check if view is returned when User's API KEY is valid in POST
    request = RequestFactory().post('', data={'API_KEY': user_key})
    request.user = user
    response = dummy_protected_view(request)
    assert response.status_code == 200

    # check if an endpoint api key is accepted
    endpoint = EndpointFactory()
    request = RequestFactory().get('', data={'API_KEY': endpoint.api_key})
    response = dummy_protected_view(request)
    assert response.status_code == 200

def test_permissions():
    user = UserFactory.create(first_name='Rebecca', last_name='Kafe', oidc_id='test_oidc_id')
    user.save()
    key = user.api_key
    
    path = reverse('api_permissions', kwargs={'user_oidc_id': user.oidc_id})
    request = RequestFactory().get(path)

    # Sanity test if the request is done without API KEY
    failed_response = permissions(request, 'definitely_invalid_oidc_id')
    assert failed_response.status_code == 403

    # Attach API KEY
    request = RequestFactory().get(path, {'API_KEY': key})

    # If the correct oidc_id is used
    response = permissions(request, user.oidc_id)
    assert response.status_code == 200
    
    # If invalid oidc_ id is used
    failed_response = permissions(request, 'definitely_invalid_oidc_id')
    assert failed_response.status_code == 404

def test_dataset_export_api():
    # Check if the API returns datasets without Exposure
    _ = DatasetFactory()
    endpoint = EndpointFactory()
    path = reverse('api_datasets')
    request = RequestFactory().get(path, {'API_KEY': endpoint.api_key})
    response = api.datasets(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 0

    # Check if the API returns datasets with Exposure
    _ = ExposureFactory(endpoint=endpoint)
    response = api.datasets(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 1

def test_project_export_api():
    # Check if the API returns projects without Exposure
    project_a = ProjectFactory()
    dataset_a = DatasetFactory(project=project_a)
    endpoint = EndpointFactory()
    path = reverse('api_projects')
    request = RequestFactory().get(path, {'API_KEY': endpoint.api_key})
    response = api.projects(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 0

    # Check if the API returns projects with Exposure
    _ = ExposureFactory(endpoint=endpoint, dataset=dataset_a)
    response = api.projects(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 1

