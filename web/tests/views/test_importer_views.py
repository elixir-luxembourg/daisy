import os

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from django.shortcuts import reverse

from core.constants import Groups


def upload_test_file(client, model_type, user=None):
    """
    Helper function to upload a test file using the provided client and return the response.
    Optionally, it logs in the given user before uploading.
    """
    if user:
        client.logout()
        client.login(username=user.username, password=user.password)

    url = reverse("import_data", args=[model_type])

    try:
        with open(
            f"{os.getcwd()}/data/demo/{model_type}.json", "rb"
        ) as test_file_content:
            uploaded_file = SimpleUploadedFile(
                f"test_file_{model_type}.json",
                test_file_content.read(),
                content_type="application/json",
            )
            response = client.post(
                url, {"file": uploaded_file}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
        return response
    except FileNotFoundError:
        pytest.fail(f"Test data file for {model_type} not found!")


@pytest.mark.parametrize(
    "model_type",
    [
        "projects",
        "datasets",
        "partners",
    ],
)
@pytest.mark.django_db
def test_importer_requests(
    user_normal,
    user_vip,
    client_user_data_steward,
    model_type,
):
    # Test POST request for data steward
    response = upload_test_file(client_user_data_steward, model_type)
    assert response.status_code == 200

    # Test GET request for data steward
    url = reverse("import_data", args=[model_type])
    response = client_user_data_steward.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 200
    assert "importer/import_form.html" in [t.name for t in response.templates]

    for user in [user_normal, user_vip]:
        # Test POST request for other users
        response = upload_test_file(client_user_data_steward, model_type, user)
        assert response.status_code == 403

        # Test GET request for other users
        client_user_data_steward.logout()
        client_user_data_steward.login(username=user.username, password=user.password)
        url = reverse("import_data", args=[model_type])
        response = client_user_data_steward.get(
            url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 403
