import json
import pytest
from io import StringIO

from core.importer.datasets_exporter import DatasetsExporter
from core.importer.partners_exporter import PartnersExporter
from core.importer.projects_exporter import ProjectsExporter
from core.importer.JSONSchemaValidator import (
    ProjectJSONSchemaValidator,
    DatasetJSONSchemaValidator,
    InstitutionJSONSchemaValidator,
)
from test import factories


def export_entities(exporter):
    buffer = exporter.export_to_buffer(StringIO())
    dict = json.loads(buffer.getvalue())
    dict_items = dict["items"]
    return dict_items


@pytest.mark.django_db
def test_export_projects(
    celery_session_worker,
    contact_types,
    partners,
    gdpr_roles,
    storage_resources,
    can_defer_constraint_checks,
):
    VIP = factories.VIPGroup()

    rebecca = factories.UserFactory.create(
        first_name="Rebecca", last_name="Kafe", groups=[VIP]
    )
    embury = factories.UserFactory.create(first_name="Embury", last_name="Bask")

    a_project = factories.ProjectFactory.create(
        acronym="Test_PRJ",
        title="Title of test project.",
        local_custodians=[rebecca, embury],
    )
    another_project = factories.ProjectFactory.create(
        acronym="Another PRJ",
        title="Title of another test project.",
        local_custodians=[rebecca, embury],
    )

    exp = ProjectsExporter(include_unpublished=False)
    project_dicts = export_entities(exp)
    assert 0 == len(project_dicts)

    exp = ProjectsExporter(include_unpublished=True)
    project_dicts = export_entities(exp)

    assert 2 == len(project_dicts)
    assert "Title of test project." == project_dicts[0]["name"]
    assert 2 == len(project_dicts[0]["contacts"])

    # TODO add check of more fields

    schema = ProjectJSONSchemaValidator()
    assert schema.validate_items(project_dicts)


@pytest.mark.django_db
def test_export_partners(
    celery_session_worker,
    contact_types,
    partners,
    gdpr_roles,
    storage_resources,
    can_defer_constraint_checks,
):
    a_partner = factories.PartnerFactory.create()

    exp = PartnersExporter(include_unpublished=False)
    partner_dicts = export_entities(exp)
    assert 96 == len(partner_dicts)  # initial data has 96 partners

    exp = PartnersExporter(include_unpublished=True)
    partner_dicts = export_entities(exp)
    assert 97 == len(partner_dicts)  # initial data has 96 partners

    # TODO add check of more fields

    schema = InstitutionJSONSchemaValidator()
    assert schema.validate_items(partner_dicts)


@pytest.mark.django_db
def test_export_datasets(
    celery_session_worker,
    contact_types,
    partners,
    gdpr_roles,
    storage_resources,
    can_defer_constraint_checks,
):
    VIP = factories.VIPGroup()
    rebecca = factories.UserFactory.create(
        first_name="Rebecca", last_name="Kafe", groups=[VIP]
    )
    embury = factories.UserFactory.create(first_name="Embury", last_name="Bask")

    a_project = factories.ProjectFactory.create(
        acronym="Test_PRJ",
        title="Title of test project.",
        local_custodians=[rebecca, embury],
    )
    a_dataset = factories.DatasetFactory.create(
        title="A test dataset", project=a_project, local_custodians=[rebecca, embury]
    )

    exp = DatasetsExporter(include_unpublished=False)
    dataset_dicts = export_entities(exp)
    assert 0 == len(dataset_dicts)

    exp = DatasetsExporter(include_unpublished=True)
    dataset_dicts = export_entities(exp)

    assert 1 == len(dataset_dicts)
    assert "A test dataset" == dataset_dicts[0]["name"]
    assert "Test_PRJ" == dataset_dicts[0]["project"]

    # TODO add check of more fields

    schema = DatasetJSONSchemaValidator()
    assert schema.validate_items(dataset_dicts)
