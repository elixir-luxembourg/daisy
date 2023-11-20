import os

import pytest

from core.importer.datasets_importer import DatasetsImporter
from core.models import Dataset, Project, DataDeclaration
from test import factories


@pytest.mark.xfail
@pytest.mark.django_db
def test_dummy(celery_session_worker, storage_resources, can_defer_constraint_checks):
    pass


@pytest.mark.django_db
def test_import_datasets(
    celery_session_worker,
    storage_resources,
    contact_types,
    data_types,
    partners,
    gdpr_roles,
    can_defer_constraint_checks,
):
    VIP = factories.VIPGroup()

    factories.UserFactory.create(
        first_name="Igor", last_name="Teal", groups=[VIP], email="user@uni.edu"
    )
    factories.UserFactory.create(
        first_name="Joanne", last_name="Swift", groups=[VIP], email="user@uni.edu"
    )
    factories.UserFactory.create(
        first_name="Elgin", last_name="Gray", groups=[VIP], email="user@uni.edu"
    )
    factories.UserFactory.create(
        first_name="Paul", last_name="Mauve", groups=[VIP], email="user@uni.edu"
    )
    factories.UserFactory.create(
        first_name="Rob", last_name="Blue", groups=[VIP], email="user@uni.edu"
    )
    factories.UserFactory.create(
        first_name="Ali", last_name="Gator", groups=[VIP], email="user@uni.edu"
    )

    data_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../data/datasets.json"
    )
    importer = DatasetsImporter(exit_on_error=True, verbose=False, validate=True)
    importer.import_json_file(data_file)

    assert 5 == Dataset.objects.all().count()
    assert 4 == Project.objects.all().count()

    d1 = Dataset.objects.filter(title="ABCD data").first()
    assert ["Igor Teal"] == [
        custodian.full_name for custodian in d1.local_custodians.all()
    ]
    assert 1 == d1.data_locations.all().count()
    shares = d1.shares.all()
    assert 1 == shares.count()

    d2 = Dataset.objects.filter(title="Hypertension data").first()
    assert ["Joanne Swift"] == [
        employee.full_name for employee in d2.local_custodians.all()
    ]
    assert "Hypertension" == d2.project.acronym
    assert 1 == d2.data_locations.all().count()

    d3 = Dataset.objects.filter(title="MDPDP data").first()
    assert ["Rob Blue"] == [
        employee.full_name for employee in d3.local_custodians.all()
    ]
    assert 2 == d3.data_locations.all().count()

    d4 = Dataset.objects.filter(title="PD data").first()
    assert ["Ali Gator"] == [
        employee.full_name for employee in d4.local_custodians.all()
    ]
    assert 7 == d4.data_locations.all().count()

    ddecs = DataDeclaration.objects.all()
    assert 5 == ddecs.count()

    ddec = DataDeclaration.objects.get(title="XYZ")
    assert "2030-05-10" == ddec.end_of_storage_duration.strftime("%Y-%m-%d")
