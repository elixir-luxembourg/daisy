from core.forms.partner import partner_label_from_instance
from test.factories import PartnerFactory


def test_label_includes_acronym_when_set():
    partner = PartnerFactory.build(name="Centre Hospitalier de Togo", acronym="CHT")
    assert partner_label_from_instance(partner) == "Centre Hospitalier de Togo (CHT)"


def test_label_is_name_only_when_acronym_blank():
    partner = PartnerFactory.build(name="Some Partner", acronym="")
    assert partner_label_from_instance(partner) == "Some Partner"
