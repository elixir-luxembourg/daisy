import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Project, Contract
from test.factories import ProjectFactory, ContractFactory


## TEST UPLOAD DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_upload_document(
    user_custodian, client_user_custodian, settings, tmpdir, model, attribute
):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir("test_upload")
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}
    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }

    response = client_user_custodian.post(url, data)
    assert response.status_code == 200
    assert response.json()["name"] == "file.txt"
    assert "id" in response.json()


@pytest.mark.skip(reason="TBD")
def test_upload_document_blank_data(user_custodian, client_user_custodian):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    # membership = MembershipFactory(project=project, contract=contract)
    # assign_perm(Permissions.EDIT.value, user_custodian, project)
    url = reverse("document_add")
    data = {"file": SimpleUploadedFile("file.txt", b"file_content")}
    response = client_user_custodian.post(url, data)
    assert response.status_code == 404


@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_upload_document_nofile(
    user_custodian, client_user_custodian, model, attribute
):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}

    # membership = MembershipFactory(project=project, contract=contract)
    # assign_perm(Permissions.EDIT.value, user_custodian, project)
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
    }
    response = client_user_custodian.post(url, data)
    assert response.status_code == 405
    assert "error" in response.json()


@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_upload_document_nopermission(
    user_custodian, client_user_normal, model, attribute
):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}

    url = reverse("document_add")
    the_file = SimpleUploadedFile("file.txt", b"file_content")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }
    response = client_user_normal.post(url, data)
    assert response.status_code == 403


## TEST DOWNLOAD DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_download_document(
    user_custodian, client_user_custodian, settings, tmpdir, model, attribute
):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir("test_upload")
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory.create(
        local_custodians=[user_custodian], project=project
    )
    entities = {"project": project, "contract": contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }

    response = client_user_custodian.post(url, data)
    pk = response.json()["id"]

    url = reverse("document_download", args=(pk,))
    assert client_user_custodian.get(url).content == b"file_content"


@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_download_document_forbidden(
    user_custodian,
    user_normal,
    client_user_custodian,
    settings,
    tmpdir,
    model,
    attribute,
):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir("test_upload")
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }

    response = client_user_custodian.post(url, data)
    pk = response.json()["id"]

    client_user_custodian.logout()
    client_user_custodian.login(username=user_normal.username, password="password")
    url = reverse("document_download", args=(pk,))
    assert client_user_custodian.get(url).status_code == 403


## TEST DELETE DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_delete_document(
    user_custodian, client_user_custodian, settings, tmpdir, model, attribute
):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir("test_delete")
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }

    response = client_user_custodian.post(url, data)
    pk = response.json()["id"]

    url = reverse("document_delete", args=(pk,))
    assert client_user_custodian.delete(url).json() == {"message": "document deleted"}


@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize(
    "model,attribute", [(Project, "project"), (Contract, "contract")]
)
def test_delete_document_forbidden(
    user_custodian,
    user_normal,
    client_user_custodian,
    settings,
    tmpdir,
    model,
    attribute,
):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir("test_delete")
    project = ProjectFactory.create(local_custodians=[user_custodian])
    contract = ContractFactory(project=project)
    entities = {"project": project, "contract": contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse("document_add")
    data = {
        "content_type": ContentType.objects.get_for_model(model).pk,
        "object_id": entities.get(attribute).pk,
        "content": the_file,
    }

    response = client_user_custodian.post(url, data)
    pk = response.json()["id"]

    client_user_custodian.logout()
    client_user_custodian.login(username=user_normal.username, password="password")

    url = reverse("document_delete", args=(pk,))
    assert client_user_custodian.delete(url).status_code == 403
