import os

import pytest

from core.importer.projects_importer import ProjectsImporter
from core.models import Project
from test import factories


@pytest.mark.django_db
def test_import_projects(celery_session_worker, contact_types, partners):

    VIP = factories.VIPGroup()

    factories.UserFactory.create(first_name='Julia', last_name='Crayon', groups=[VIP])
    factories.UserFactory.create(first_name='Rebecca', last_name='Kafe', groups=[VIP])
    factories.UserFactory.create(first_name='Embury', last_name='Bask')


    factories.UserFactory.create(first_name='Colman', last_name='Level', groups=[VIP])
    factories.UserFactory.create(first_name='Nic', last_name='Purple', groups=[VIP])
    factories.UserFactory.create(first_name='James', last_name='BK')

    projects_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/projects.json")
    importer = ProjectsImporter(exit_on_error=True, verbose=False, validate=True)
    importer.import_json_file(projects_json)
    
    projects = Project.objects.all()
    assert 2 == projects.count()
    project1 = Project.objects.filter(acronym='In vitro disease modeling').first()
    assert ["Joanne Swift", "Rebecca Kafe"] == [custodian.full_name for custodian in project1.local_custodians.all()]
    assert 1 == project1.company_personnel.count()
    assert False == project1.has_cner
    assert True == project1.has_erp
    assert ["Embury Bask"] == [employee.full_name for employee in project1.company_personnel.all()]
    assert "test notes 123" == project1.erp_notes
    assert 2 == project1.publications.count()

    project2 = Project.objects.filter(acronym='CCCC deficiency').first()
    assert ["Colman Level"] == [custodian.full_name for custodian in project2.local_custodians.all()]
    assert 3 == project2.company_personnel.count()
    assert 1 == project2.publications.count()
    #2016-11-01
    assert 2016 == project2.start_date.year
    assert 11 == project2.start_date.month
    assert 1  == project2.start_date.day
    assert 1 == project2.publications.count()


@pytest.mark.django_db
def test_process_publication(*args, **kwargs):
    pass