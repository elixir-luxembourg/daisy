import pytest

from test.factories import (
    ContractFactory,
    PartnerFactory,
    PartnerRoleFactory,
    ProjectFactory,
)


@pytest.mark.django_db
def test_short_name_lists_partners_from_roles():
    contract = ContractFactory(project=ProjectFactory(acronym="PROJ"))
    contract.partners_roles.all().delete()
    PartnerRoleFactory(
        contract=contract, partner=PartnerFactory(name="Acme", elu_accession="ACME")
    )
    PartnerRoleFactory(
        contract=contract, partner=PartnerFactory(name="Globex", elu_accession="GLOBEX")
    )

    result = contract.short_name()

    assert result.startswith("Contract with ")
    assert result.endswith('- "PROJ"')
    assert "Acme" in result and "Globex" in result


@pytest.mark.django_db
def test_short_name_falls_back_without_partners():
    contract = ContractFactory(project=ProjectFactory(acronym="PROJ"))
    contract.partners_roles.all().delete()

    assert contract.short_name() == 'Contract with Undefined partner(s) - "PROJ"'
