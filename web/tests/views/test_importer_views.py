import os
from typing import Optional
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from django.contrib.auth.models import Group
from django.shortcuts import reverse
from django.test.client import Client
from core.constants import Groups
from test.factories import DataStewardGroup, UserFactory
from core.models.user import User


def login_test_user(
    test_client: Client, user: User, password: Optional[str] = "test-user"
):
    assert test_client.login(username=user.username, password=password), "Login failed"


@pytest.mark.parametrize(
    "group, model_type",
    [
        (DataStewardGroup, "projects"),
        (DataStewardGroup, "datasets"),
        (DataStewardGroup, "partners"),
    ],
)
@pytest.mark.django_db
def test_importer_get_request(group, model_type):
    """
    Test the GET request to the import_data endpoint for different model types.

    The test checks if users belonging to the DataStewardGroup can successfully
    access the importer's form via AJAX requests for different model types
    (projects, datasets, and partners).

    Args:
        group (Group): The user group, expected to be DataStewardGroup.
        model_type (str): The model type which can be 'projects', 'datasets', or 'partners'.
    """
    user = UserFactory(groups=[group()])
    client = Client()
    login_test_user(client, user)
    url = reverse("import_data", args=[model_type])
    response = client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    if user.is_part_of(Group.objects.get(name=Groups.DATA_STEWARD.value)):
        assert response.status_code == 200
    assert "importer/import_form.html" in [t.name for t in response.templates]
    client.logout()


@pytest.mark.parametrize(
    "group, model_type",
    [
        (DataStewardGroup, "projects"),
        (DataStewardGroup, "datasets"),
        (DataStewardGroup, "partners"),
    ],
)
@pytest.mark.django_db
def test_importer_post_request(group, model_type):
    """
    Test the POST request to the import_data endpoint for different model types.

    The test verifies if users belonging to the DataStewardGroup can successfully
    post data (in this case, JSON files) for different model types (projects, datasets,
    and partners) and get a successful 200 response via AJAX requests.

    Args:
        group (Group): The user group, expected to be DataStewardGroup.
        model_type (str): The model type which can be 'projects', 'datasets', or 'partners'.
    """
    user = UserFactory(groups=[group()])
    client = Client()
    login_test_user(client, user)
    url = reverse("import_data", args=[model_type])
    with open(f"{os.getcwd()}/data/demo/{model_type}.json", "rb") as test_file_content:
        uploaded_file = SimpleUploadedFile(
            f"test_file_{model_type}.json",
            test_file_content.read(),
            content_type="application/json",
        )
        response = client.post(
            url, {"file": uploaded_file}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 200
    client.logout()
