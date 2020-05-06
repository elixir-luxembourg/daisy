import os

import pytest
from django.conf import settings

from core.importer.elx_submission_importer import DishSubmissionImporter
from core.models import Dataset, Project
from test import factories

TEST_DATA_PATH = os.path.join(settings.BASE_DIR, 'core', 'tests', 'data')


@pytest.mark.django_db
def test_import_submission(celery_session_worker, partners, gdpr_roles, can_defer_constraint_checks):
    VIP = factories.VIPGroup()
    reinhard = factories.UserFactory.create(first_name='Rene', last_name='Sahoo', groups=[VIP])

    factories.UserFactory.create(first_name='Elgin', last_name='Gray', groups=[VIP])
    factories.UserFactory.create(first_name='Rob', last_name='Blue', groups=[VIP])
    elixir_project = factories.ProjectFactory.create(acronym='ELIXIR', title='ELIXIR', local_custodians=[reinhard])
    dataset_json = os.path.join(TEST_DATA_PATH,
                                "ELX_LU_SUB-1.json")

    with open(dataset_json, "r") as file_with_dataset:
        importer = DishSubmissionImporter(elixir_project.title)
        importer.import_json(file_with_dataset.read(), True, True)
    assert 1 == Dataset.objects.all().count()
    # assert 2 == Project.objects.all().count()
    dataset = Dataset.objects.first()
    assert 'ELX_LU_SUB-1' == dataset.title
    # assert 2 == dataset.data_declarations.all().count()
    # TODO finalise Submission importer once elixir-dcp i.e. DISH goes into production.
    # Mapping from DISH to DAISY not yet complete...
    assert 'ELIXIR' == dataset.project.title
    assert 2 == dataset.local_custodians.all().count()
    assert ["Elgin Gray", "Rob Blue"] == [custodian.full_name for custodian in dataset.local_custodians.all()]
