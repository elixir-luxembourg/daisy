import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Project, Contract
from test.factories import ProjectFactory, ContractFactory


## TEST UPLOAD DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_upload_document(user_vip, client_user_vip, settings, tmpdir, model, attribute):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir('test_upload')
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}
    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }

    response = client_user_vip.post(url, data)
    assert response.status_code == 200
    assert response.json()['name'] == "file.txt"
    assert 'id' in response.json()

@pytest.mark.skip(reason="TBD")
def test_upload_document_blank_data(user_vip, client_user_vip):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    # membership = MembershipFactory(project=project, contract=contract)
    # assign_perm(Permissions.EDIT.value, user_vip, project)
    url = reverse('document_add')
    data = {
        'file': SimpleUploadedFile("file.txt", b"file_content")
    }
    response = client_user_vip.post(url, data)
    assert response.status_code == 404

@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_upload_document_nofile(user_vip, client_user_vip, model, attribute):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}

    # membership = MembershipFactory(project=project, contract=contract)
    # assign_perm(Permissions.EDIT.value, user_vip, project)
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
    }
    response = client_user_vip.post(url, data)
    assert response.status_code == 405
    assert 'error' in response.json()

@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_upload_document_nopermission(user_vip, client_user_normal, model, attribute):
    """
    Test view for uploading doc.
    """
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}

    url = reverse('document_add')
    the_file = SimpleUploadedFile("file.txt", b"file_content")
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }
    response = client_user_normal.post(url, data)
    assert response.status_code == 403


## TEST DOWNLOAD DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_download_document(user_vip, client_user_vip, settings, tmpdir, model, attribute):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir('test_upload')
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory.create(local_custodians=[user_vip], project=project)
    entities = {'project': project, 'contract': contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }

    response = client_user_vip.post(url, data)
    pk = response.json()['id']

    url = reverse('document_download', args=(pk,))
    assert client_user_vip.get(url).content == b"file_content"

@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_download_document_forbidden(user_vip, user_normal, client_user_vip, settings, tmpdir, model, attribute):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir('test_upload')
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }

    response = client_user_vip.post(url, data)
    pk = response.json()['id']

    client_user_vip.logout()
    client_user_vip.login(username=user_normal.username, password=user_normal.password)
    url = reverse('document_download', args=(pk,))
    assert client_user_vip.get(url).status_code == 403


## TEST DELETE DOCUMENT
@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_delete_document(user_vip, client_user_vip, settings, tmpdir, model, attribute):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir('test_delete')
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }

    response = client_user_vip.post(url, data)
    pk = response.json()['id']

    url = reverse('document_delete', args=(pk,))
    assert client_user_vip.delete(url).json() == {'message': 'document deleted'}

@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('model,attribute', [
    (Project, 'project'),
    (Contract, 'contract')
])
def test_delete_document_forbidden(user_vip, user_normal, client_user_vip, settings, tmpdir, model, attribute):
    """
    Test view for uploading doc.
    """
    settings.MEDIA_ROOT = tmpdir.mkdir('test_delete')
    project = ProjectFactory.create(local_custodians=[user_vip])
    contract = ContractFactory(project=project)
    entities = {'project': project, 'contract': contract}

    the_file = SimpleUploadedFile("file.txt", b"file_content")
    url = reverse('document_add')
    data = {
        'content_type': ContentType.objects.get_for_model(model).pk,
        'object_id': entities.get(attribute).pk,
        'content': the_file
    }

    response = client_user_vip.post(url, data)
    pk = response.json()['id']

    client_user_vip.logout()
    client_user_vip.login(username=user_normal.username, password=user_normal.password)

    url = reverse('document_delete', args=(pk,))
    assert client_user_vip.delete(url).status_code == 403
