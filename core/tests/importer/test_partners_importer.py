import pytest

from core.importer.partners_importer import PartnersImporter
from core.models import Partner


def _institution_dict(**overrides):
    data = {
        "name": "Centre Hospitalier de Togo",
        "external_id": "ELU_I_19309",
        "acronym": "CHT",
        "is_clinical": True,
        "geo_category": "National",
        "sector_category": "PUBLIC",
        "address": "Ave De La 6, Espoir Vie Togo, Lome",
        "country_code": "TO",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_import_sets_acronym_when_present():
    PartnersImporter().process_json(_institution_dict())

    partner = Partner.objects.get(elu_accession="ELU_I_19309")
    assert partner.acronym == "CHT"


@pytest.mark.django_db
def test_import_sets_empty_acronym_when_null():
    PartnersImporter().process_json(_institution_dict(acronym=None))

    partner = Partner.objects.get(elu_accession="ELU_I_19309")
    assert partner.acronym == ""


@pytest.mark.django_db
def test_import_sets_empty_acronym_when_missing():
    data = _institution_dict()
    del data["acronym"]
    PartnersImporter().process_json(data)

    partner = Partner.objects.get(elu_accession="ELU_I_19309")
    assert partner.acronym == ""
