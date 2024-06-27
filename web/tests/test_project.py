import pytest
from django.urls import reverse

from core import constants
from core.models import Project
from test import factories


def login(client, user):
    """
    Shotcut to log an user to a client.
    """
    assert client.login(
        username=user.username, password=user.password
    ), f"Login of user {user.username} failed"


@pytest.mark.parametrize("is_vip", [True, False])
def test_project_create_get(client, is_vip, user_vip, user_normal):
    """
    GET url for project creation.
    """
    url = reverse("project_add")
    is_vip and login(client, user_vip) or login(client, user_normal)
    response = client.get(url)
    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name


@pytest.mark.parametrize("is_vip", [True, False])
def test_project_create_post_valid(permissions, client, user_vip, user_normal, is_vip):
    """
    POST to project creation
    """
    url = reverse("project_add")
    data = {
        "acronym": "acronym",
        "title": "title",
        "description": "description",
        "local_custodians": is_vip and [] or [user_vip.pk],
        "start_date": "2018-10-30",
        "end_date": "2018-12-30",
        "erp_notes": "erp is not needed for test",
        "company_personnel": [],
        "legal_documents": [],
        "publications": [],
    }
    is_vip and login(client, user_vip) or login(client, user_normal)
    response = client.post(url, data)

    # check redirect and project is created
    assert response.status_code == 302
    project = Project.objects.first()
    assert project is not None
    assert response.url == reverse("project", args=(project.pk,))

    # check if normal user has proper right
    if not is_vip:
        assert user_normal.has_permission_on_object(
            f"core.{constants.Permissions.EDIT.value}_project", project
        )
        assert user_normal.has_permission_on_object(
            f"core.{constants.Permissions.DELETE.value}_project", project
        )

    # pi should always have the perms
    assert user_vip.has_permission_on_object(
        f"core.{constants.Permissions.EDIT.value}_project", project
    )
    assert user_vip.has_permission_on_object(
        f"core.{constants.Permissions.ADMIN.value}_project", project
    )
    assert user_vip.has_permission_on_object(
        f"core.{constants.Permissions.DELETE.value}_project", project
    )


@pytest.mark.parametrize("is_vip", [True, False])
def test_project_create_post_blank(client, user_normal, user_vip, is_vip):
    url = reverse("project_add")
    data = {}
    is_vip and login(client, user_vip) or login(client, user_normal)
    response = client.post(url, data)

    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name


@pytest.mark.parametrize("is_vip", [True, False])
def test_project_create_post_invalid(client, user_normal, user_vip, is_vip):
    url = reverse("project_add")
    data = {
        "title": "title",
        "description": "description",
        "local_custodians": is_vip and [] or [user_vip.pk],
        "start_date": "2018-10",
        "end_date": "2018-12-30",
        "company_personnel": [],
        "legal_documents": [],
        "publications": [],
    }
    is_vip and login(client, user_vip) or login(client, user_normal)
    response = client.post(url, data)

    assert response.status_code == 200
    assert "projects/project_form.html" in response.template_name
