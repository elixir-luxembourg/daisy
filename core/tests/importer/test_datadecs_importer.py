import os

import pytest

from core.importer.datadecs_importer import DatadecsImporter
from core.importer.datasets_importer import DatasetsImporter
from core.models import Dataset, DataDeclaration
from test import factories


@pytest.mark.xfail
@pytest.mark.django_db
def test_dummy(celery_session_worker, storage_resources, can_defer_constraint_checks):
    pass


@pytest.mark.django_db
def test_import_datadecs(celery_session_worker, contact_types, partners, gdpr_roles, storage_resources, can_defer_constraint_checks):

    VIP = factories.VIPGroup()

    factories.UserFactory.create(first_name='Igor', last_name='Teal', groups=[VIP])
    factories.UserFactory.create(first_name='Joanne', last_name='Swift', groups=[VIP])
    factories.UserFactory.create(first_name='Elgin', last_name='Gray', groups=[VIP])
    factories.UserFactory.create(first_name='Paul', last_name='Mauve', groups=[VIP])
    factories.UserFactory.create(first_name='Rene', last_name='Sahoo', groups=[VIP])
    factories.UserFactory.create(first_name='Rob', last_name='Blue', groups=[VIP])

    dataset_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/datasets.json")
    with open(dataset_file, "r") as f:
        importer = DatasetsImporter()
        importer.import_json(f.read(), True)

    datadec_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/datadecs.json")
    with open(datadec_file, "r") as f:
        importer = DatadecsImporter()
        importer.import_json(f.read(), True)

    dsets = Dataset.objects.all()
    assert 5 == dsets.count()

    ddecs = DataDeclaration.objects.all()
    HyperData = ddecs[1]
    assert 'Hypertension-ABC disease' == HyperData.title
    contract = HyperData.contract
    first_partner_role = contract.partners_roles.first()
    assert first_partner_role.contacts.count() > 0
    assert "Alberto" == first_partner_role.contacts.first().first_name
    assert "Pico" == first_partner_role.contacts.first().last_name
    assert "Hypertension" == contract.project.acronym
    assert "ELU_I_94" == first_partner_role.partner.elu_accession
