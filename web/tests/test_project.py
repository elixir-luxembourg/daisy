from django.urls import reverse

from core import constants
from core.models import Project


def login(client, user):
    """
    Shotcut to log an user to a client.
    """
    assert client.login(
        username=user.username, password="password"
    ), f"Login of user {user.username} failed"


def test_project_create_get(client, user_normal):
    """
    GET url for project creation.
    """
    url = reverse("project_add")
    login(client, user_normal)
    response = client.get(url)
    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name


def test_project_create_post_valid(permissions, client, user_custodian, user_normal):
    """
    POST to project creation
    """
    url = reverse("project_add")
    data = {
        "acronym": "acronym",
        "title": "title",
        "description": "description",
        "local_custodians": [user_custodian.pk],
        "start_date": "2018-10-30",
        "end_date": "2018-12-30",
        "erp_notes": "erp is not needed for test",
        "company_personnel": [],
        "legal_documents": [],
        "publications": [],
    }
    login(client, user_normal)
    response = client.post(url, data)

    # check redirect and project is created
    assert response.status_code == 302
    project = Project.objects.first()
    assert project is not None
    assert response.url == reverse("project", args=(project.pk,))

    # the author of the project keeps the rights on it
    assert user_normal.has_permission_on_object(
        f"core.{constants.Permissions.EDIT.value}_project", project
    )
    assert user_normal.has_permission_on_object(
        f"core.{constants.Permissions.DELETE.value}_project", project
    )

    # the local custodian has the rights too
    assert user_custodian.has_permission_on_object(
        f"core.{constants.Permissions.EDIT.value}_project", project
    )
    assert user_custodian.has_permission_on_object(
        f"core.{constants.Permissions.ADMIN.value}_project", project
    )
    assert user_custodian.has_permission_on_object(
        f"core.{constants.Permissions.DELETE.value}_project", project
    )


def test_project_create_post_blank(client, user_normal):
    url = reverse("project_add")
    data = {}
    login(client, user_normal)
    response = client.post(url, data)

    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name


def test_project_create_post_invalid(client, user_custodian, user_normal):
    url = reverse("project_add")
    data = {
        "title": "title",
        "description": "description",
        "local_custodians": [user_custodian.pk],
        "start_date": "2018-10",
        "end_date": "2018-12-30",
        "company_personnel": [],
        "legal_documents": [],
        "publications": [],
    }
    login(client, user_normal)
    response = client.post(url, data)

    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name
