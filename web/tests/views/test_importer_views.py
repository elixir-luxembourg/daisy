import os
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from django.shortcuts import reverse

from .utils import login_test_user


def upload_test_file(client, model_type, user, file_name=None):
    """
    Helper function to upload a test file using the provided client and return the response.
    Optionally, it logs in the given user before uploading.
    """
    client.logout()
    login_test_user(client, user, "password")

    url = reverse("import_data", args=[model_type])

    try:
        with open(
            f"{os.getcwd()}/data/demo/{file_name if file_name else model_type}.json",
            "rb",
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
@pytest.mark.parametrize(
    "user_type, expected_status_code",
    [
        ("user_data_steward", 200),
        ("user_normal", 403),
        ("user_legal", 403),
        ("user_auditor", 403),
        ("user_vip", 403),
    ],
)
@pytest.mark.django_db
def test_importer_requests(
    model_type,
    user_type,
    expected_status_code,
    client,
    request,
):
    # Running fixture to get user
    user = request.getfixturevalue(user_type)

    # Test POST request for all users
    response = upload_test_file(client, model_type, user)
    assert response.status_code == expected_status_code

    # Test GET request for data steward
    url = reverse("import_data", args=[model_type])
    response = client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == expected_status_code
    if expected_status_code == 200:
        assert "importer/import_form.html" in [t.name for t in response.templates]

    # Test POST request for an invalid file
    if user.username == "data.steward":
        response = upload_test_file(client, model_type, user, file_name="elu-core")
        assert "Error:" in response.content.decode(
            "utf-8"
        ), "Unexpected response: 'Error:' not found in content"
