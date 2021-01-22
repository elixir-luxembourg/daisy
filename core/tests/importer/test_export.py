import json
import pytest
from io import StringIO

from core.importer.datasets_exporter import DatasetsExporter
from core.importer.partners_exporter import PartnersExporter
from core.importer.projects_exporter import ProjectsExporter
from core.importer.JSONSchemaValidator import ProjectJSONSchemaValidator, DatasetJSONSchemaValidator,  InstitutionJSONSchemaValidator
from test import factories


@pytest.mark.django_db
def test_export_projects(celery_session_worker, contact_types, partners, gdpr_roles, storage_resources, can_defer_constraint_checks):

    VIP = factories.VIPGroup()

    rebecca = factories.UserFactory.create(first_name='Rebecca', last_name='Kafe', groups=[VIP])
    embury = factories.UserFactory.create(first_name='Embury', last_name='Bask')

    a_project =  factories.ProjectFactory.create(acronym='Test_PRJ', title='Title of test project.', local_custodians=[rebecca, embury])
    another_project =  factories.ProjectFactory.create(acronym='Another PRJ', title='Title of another test project.', local_custodians=[rebecca, embury])

    exp = ProjectsExporter()
    buffer = exp.export_to_buffer(StringIO())

    dict = json.loads(buffer.getvalue())
    project_dicts = dict['items']
    assert 2 == len(project_dicts)

    assert "Title of test project." ==  project_dicts[0]['name']
    assert 2 == len(project_dicts[0]['contacts'])

    #TODO add check of more fields

    schema = ProjectJSONSchemaValidator()
    assert schema.validate_items(project_dicts)


@pytest.mark.django_db
def test_export_partners(celery_session_worker, contact_types, partners, gdpr_roles, storage_resources, can_defer_constraint_checks):


    exp = PartnersExporter()
    buffer = exp.export_to_buffer(StringIO())

    dict = json.loads(buffer.getvalue())
    partner_dicts = dict['items']
    assert 96 == len(partner_dicts) # initial data has 96 partners

    #TODO add check of more fields

    schema = InstitutionJSONSchemaValidator()
    assert schema.validate_items(partner_dicts)


@pytest.mark.django_db
def test_export_datasets(celery_session_worker, contact_types, partners, gdpr_roles, storage_resources, can_defer_constraint_checks):


    VIP = factories.VIPGroup()
    rebecca = factories.UserFactory.create(first_name='Rebecca', last_name='Kafe', groups=[VIP])
    embury = factories.UserFactory.create(first_name='Embury', last_name='Bask')

    a_project =  factories.ProjectFactory.create(acronym='Test_PRJ', title='Title of test project.', local_custodians=[rebecca, embury])
    a_dataset =  factories.DatasetFactory.create(title='A test dataset', project=a_project, local_custodians=[rebecca, embury])


    exp = DatasetsExporter()
    buffer = exp.export_to_buffer(StringIO())

    dict = json.loads(buffer.getvalue())
    dataset_dicts = dict['items']
    assert 1 == len(dataset_dicts)
    assert "A test dataset" == dataset_dicts[0]['name']
    assert "Test_PRJ" == dataset_dicts[0]['project']

    #TODO add check of more fields

    schema = DatasetJSONSchemaValidator()
    assert schema.validate_items(dataset_dicts)
