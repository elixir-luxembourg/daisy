from json import loads

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from web.views import api

from test.factories import (
    UserFactory,
    EndpointFactory,
    DatasetFactory,
    ExposureFactory,
    ProjectFactory,
    PartnerFactory,
    CohortFactory,
    ContractFactory,
)
from core.constants import Permissions
from core.models import DiseaseTerm
from web.views.api import create_error_response, protect_api


def test_create_error_response():
    assert type(create_error_response("test")) == JsonResponse
    assert create_error_response("test").status_code == 500
    assert create_error_response("test", status=501).status_code == 501

    body = loads(
        create_error_response("description_value", {"more": "information"}).content
    )
    assert body.get("description") == "description_value"
    assert body.get("more") == "information"


def test_protect_api_decorator():
    user = UserFactory.create(first_name="Rebecca", last_name="Kafe")
    user.save()
    user_key = user.api_key
    global_key = getattr(settings, "GLOBAL_API_KEY", "test_global_key")
    endpoint = EndpointFactory()
    captured = {}

    @protect_api()
    def dummy_view(request):
        captured["api_user"] = getattr(request, "api_user", None)
        return JsonResponse("Success", safe=False)

    @protect_api(write_required=True)
    def dummy_write_view(request):
        return JsonResponse("Success", safe=False)

    factory = RequestFactory()

    assert dummy_view(factory.get("", {"API_KEY": global_key})).status_code == 200
    assert dummy_view(factory.get("", HTTP_X_API_KEY=global_key)).status_code == 200

    assert dummy_view(factory.get("", {"API_KEY": endpoint.api_key})).status_code == 200
    assert (
        dummy_view(factory.get("", HTTP_X_API_KEY=endpoint.api_key)).status_code == 200
    )

    assert dummy_view(factory.get("")).status_code == 401
    assert dummy_view(factory.get("", {"API_KEY": "wrong-api-key"})).status_code == 401

    # user api-key sets request.api_user
    assert dummy_view(factory.get("", {"API_KEY": user_key})).status_code == 200
    assert captured["api_user"] == user
    assert dummy_view(factory.get("", HTTP_X_API_KEY=user_key)).status_code == 200
    assert captured["api_user"] == user

    # user api-key on non-GET
    assert dummy_view(factory.post("", {"API_KEY": user_key})).status_code == 403
    assert dummy_view(factory.post("", HTTP_X_API_KEY=user_key)).status_code == 403

    # write_required decorator requires global api-key
    assert (
        dummy_write_view(factory.post("", {"API_KEY": global_key})).status_code == 200
    )
    assert dummy_write_view(factory.get("", {"API_KEY": user_key})).status_code == 403
    assert dummy_write_view(factory.post("", {"API_KEY": user_key})).status_code == 403


def test_permissions():
    user = UserFactory.create(
        first_name="Rebecca", last_name="Kafe", oidc_id="test_oidc_id"
    )
    user.save()
    key = user.api_key

    path = reverse("api_permissions", kwargs={"user_oidc_id": user.oidc_id})

    # Sanity test if the request is done without API KEY
    request = RequestFactory().get(path)
    failed_response = api.permissions(request, "definitely_invalid_oidc_id")
    assert failed_response.status_code == 401

    # Attach API KEY
    request = RequestFactory().get(path, {"API_KEY": key})

    # If the correct oidc_id is used
    response = api.permissions(request, user.oidc_id)
    assert response.status_code == 200

    # If invalid oidc_ id is used
    failed_response = api.permissions(request, "definitely_invalid_oidc_id")
    assert failed_response.status_code == 404


def test_dataset_export_api():
    # Check if the API returns datasets without Exposure
    _ = DatasetFactory()
    endpoint = EndpointFactory()
    path = reverse("api_datasets")
    request = RequestFactory().get(path, {"API_KEY": endpoint.api_key})
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
    path = reverse("api_projects")
    request = RequestFactory().get(path, {"API_KEY": endpoint.api_key})
    response = api.projects(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 0

    # Check if the API returns projects with Exposure
    _ = ExposureFactory(endpoint=endpoint, dataset=dataset_a)
    response = api.projects(request)
    assert response.status_code == 200
    assert len(loads(response.content).get("items")) == 1


def test_project_export_api_with_fields():
    project = ProjectFactory(title="Test Project", acronym="TEST")
    endpoint = EndpointFactory()
    ExposureFactory(endpoint=endpoint, dataset=DatasetFactory(project=project))
    path = reverse("api_projects")

    # with fields
    request = RequestFactory().get(
        path, {"API_KEY": endpoint.api_key, "fields": "acronym,name"}
    )
    response = api.projects(request)
    test_project = loads(response.content).get("items")[0]

    assert response.status_code == 200
    assert len(test_project) == 3
    assert "acronym" in test_project
    assert "name" in test_project
    assert "source" in test_project
    assert not "description" in test_project

    # without fields
    request = RequestFactory().get(path, {"API_KEY": endpoint.api_key})
    response = api.projects(request)
    test_project = loads(response.content).get("items")[0]

    assert response.status_code == 200
    assert len(test_project) == 15
    assert "description" in test_project


def test_partners_public_access():
    PartnerFactory(name="Published Partner", _is_published=True)
    PartnerFactory(name="Unpublished Partner", _is_published=False)
    request = RequestFactory().get(reverse("api_partners"))
    response = api.partners(request)
    first_results = loads(response.content).get("results")

    assert response.status_code == 200
    assert len(first_results) == 1
    assert first_results[0]["name"] == "Published Partner"

    # with fields
    request = RequestFactory().get(reverse("api_partners"), {"fields": "name"})
    partner_dict = loads(api.partners(request).content).get("results")[0]

    assert all(field in partner_dict for field in ["name", "acronym", "address"])

    # with published
    request = RequestFactory().get(reverse("api_partners"), {"published": "true"})
    result = loads(api.partners(request).content).get("results")

    assert result == first_results


def test_partners_published_with_apikey():
    user = UserFactory.create()
    PartnerFactory(name="Published Partner", _is_published=True)
    PartnerFactory(name="Unpublished Partner", _is_published=False)
    path = reverse("api_partners")

    # without published filter
    request = RequestFactory().get(path, {"API_KEY": user.api_key})
    response = api.partners(request)
    results = loads(response.content).get("results")

    assert response.status_code == 200
    assert len(results) == 2
    assert results[0]["name"] == "Published Partner"
    assert results[1]["name"] == "Unpublished Partner"

    # with published=true filter
    request = RequestFactory().get(path, {"API_KEY": user.api_key, "published": "true"})
    results = loads(api.partners(request).content).get("results")

    assert len(results) == 1
    assert results[0]["name"] == "Published Partner"

    # with published=false filter
    request = RequestFactory().get(
        path, {"API_KEY": user.api_key, "published": "false"}
    )
    results = loads(api.partners(request).content).get("results")

    assert len(results) == 1
    assert results[0]["name"] == "Unpublished Partner"


def test_partners_fields_with_apikey():
    user = UserFactory.create()
    PartnerFactory(
        name="Test Partner", acronym="TP", address="123 Test St", _is_published=True
    )
    path = reverse("api_partners")

    # with fields
    request = RequestFactory().get(
        path, {"API_KEY": user.api_key, "fields": "name,acronym"}
    )
    response = api.partners(request)
    partner_dict = loads(response.content).get("results")[0]

    assert response.status_code == 200
    assert all(field in partner_dict for field in ["name", "acronym"])
    assert not "address" in partner_dict
    assert not "geo_category" in partner_dict

    # without fields
    request = RequestFactory().get(path, {"API_KEY": user.api_key})
    partner_dict = loads(api.partners(request).content).get("results")[0]

    assert "name" in partner_dict
    assert "acronym" in partner_dict


def test_cohorts_endpoint():
    CohortFactory(title="Published Cohort", _is_published=True)
    CohortFactory(title="Unpublished Cohort", _is_published=False)

    request = RequestFactory().get(reverse("api_cohorts"))
    response = api.cohorts(request)
    results = loads(response.content).get("results")

    assert response.status_code == 200
    assert len(results) == 1
    assert results[0]["name"] == "Published Cohort"


def test_users_endpoint():
    UserFactory(username="testuser1", first_name="Test", last_name="User1")
    UserFactory(username="testuser2", first_name="Test", last_name="User2")

    request = RequestFactory().get(reverse("api_users"))
    response = api.users(request)
    results = loads(response.content).get("results")

    assert response.status_code == 200
    assert len(results) >= 2
    assert all("id" in r and "text" in r for r in results)


def test_termsearch_endpoint():
    DiseaseTerm.objects.create(label="Diabetes Mellitus", term_id="TEST:001")
    DiseaseTerm.objects.create(label="Diabetes Type 2", term_id="TEST:002")
    DiseaseTerm.objects.create(label="Cancer", term_id="TEST:003")

    path = reverse("api_termsearch", kwargs={"category": "disease"})
    request = RequestFactory().get(path, {"search": "Diabetes", "page": 1})
    response = api.termsearch(request, "disease")
    data = loads(response.content)

    assert response.status_code == 200
    assert len(data.get("results")) == 2
    assert all("Diabetes" in r["text"] for r in data["results"])
    assert "pagination" in data
    assert "pagination" in data


def test_contracts_endpoint():
    project = ProjectFactory()
    dataset = DatasetFactory(project=project)
    ContractFactory(project=project)
    endpoint = EndpointFactory()
    ExposureFactory(dataset=dataset, endpoint=endpoint)

    path = reverse("api_contracts")
    request = RequestFactory().get(path, {"API_KEY": endpoint.api_key})
    response = api.contracts(request)
    items = loads(response.content).get("items")

    assert response.status_code == 200
    assert len(items) >= 1
    assert items[0]["project_id"] == project.id


def test_datasets_user_permission_filtering(permissions):
    user = UserFactory()
    dataset1 = DatasetFactory(title="Accessible Dataset")
    dataset2 = DatasetFactory(title="Inaccessible Dataset")

    assign_perm(f"core.{Permissions.PROTECTED.value}_dataset", user, dataset1)

    endpoint = EndpointFactory()
    ExposureFactory(dataset=dataset1, endpoint=endpoint)
    ExposureFactory(dataset=dataset2, endpoint=endpoint)

    path = reverse("api_datasets")
    request = RequestFactory().get(path, {"API_KEY": user.api_key})
    response = api.datasets(request)
    items = loads(response.content).get("items")

    assert response.status_code == 200
    assert len(items) == 1
    assert items[0]["name"] == "Accessible Dataset"


def test_projects_user_permission_filtering(permissions):
    user = UserFactory()
    project1 = ProjectFactory(title="Accessible Project")
    project2 = ProjectFactory(title="Inaccessible Project")
    dataset1 = DatasetFactory(project=project1)
    dataset2 = DatasetFactory(project=project2)

    assign_perm(f"core.{Permissions.PROTECTED.value}_project", user, project1)

    endpoint = EndpointFactory()
    ExposureFactory(dataset=dataset1, endpoint=endpoint)
    ExposureFactory(dataset=dataset2, endpoint=endpoint)

    path = reverse("api_projects")
    request = RequestFactory().get(path, {"API_KEY": user.api_key})
    response = api.projects(request)
    items = loads(response.content).get("items")

    assert response.status_code == 200
    assert len(items) == 1
    assert items[0]["name"] == "Accessible Project"


def test_contracts_user_permission_filtering(permissions):
    user = UserFactory()
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    dataset1 = DatasetFactory(project=project1)
    dataset2 = DatasetFactory(project=project2)
    contract1 = ContractFactory(project=project1)
    ContractFactory(project=project2)

    assign_perm(f"core.{Permissions.PROTECTED.value}_contract", user, contract1)

    endpoint = EndpointFactory()
    ExposureFactory(dataset=dataset1, endpoint=endpoint)
    ExposureFactory(dataset=dataset2, endpoint=endpoint)

    path = reverse("api_contracts")
    request = RequestFactory().get(path, {"API_KEY": user.api_key})
    response = api.contracts(request)
    items = loads(response.content).get("items")

    assert response.status_code == 200
    assert len(items) == 1
    assert items[0]["project_id"] == project1.id


def test_global_api_key_bypasses_permissions(permissions):
    global_key = settings.GLOBAL_API_KEY
    dataset1 = DatasetFactory(title="Dataset 1")
    dataset2 = DatasetFactory(title="Dataset 2")
    endpoint = EndpointFactory()
    ExposureFactory(dataset=dataset1, endpoint=endpoint)
    ExposureFactory(dataset=dataset2, endpoint=endpoint)

    path = reverse("api_datasets")
    request = RequestFactory().get(path, {"API_KEY": global_key})
    response = api.datasets(request)
    items = loads(response.content).get("items")

    assert response.status_code == 200
    assert len(items) == 2


def test_api_key_required():
    path = reverse("api_datasets")
    request = RequestFactory().get(path)
    response = api.datasets(request)

    assert response.status_code == 401
    assert "API key required" in loads(response.content).get("description")


def test_write_operations_require_global_key():
    user = UserFactory()
    path = reverse("api_keycloak_force")
    request = RequestFactory().post(path, {"API_KEY": user.api_key})
    response = api.force_keycloak_synchronization(request)

    assert response.status_code == 403
    assert "global api key" in loads(response.content).get("description", "").lower()
