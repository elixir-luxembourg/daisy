import pytest

from test.factories import (
    DataDeclarationFactory,
    DataLocationFactory,
    DatasetFactory,
    LegalBasisFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_missing_records_lists_every_gap():
    dataset = DatasetFactory()

    assert dataset.missing_records == [
        "Legal basis",
        "Data declaration",
        "Storage",
        "Custodian",
    ]
    assert dataset.is_record_complete is False


@pytest.mark.django_db
def test_missing_records_empty_when_complete():
    dataset = DatasetFactory(local_custodians=[UserFactory()])
    LegalBasisFactory(dataset=dataset)
    DataDeclarationFactory(dataset=dataset)
    DataLocationFactory(dataset=dataset)

    assert dataset.missing_records == []
    assert dataset.is_record_complete is True
