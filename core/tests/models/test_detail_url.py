import pytest
from django.apps import apps
from test import factories

MODELS = (
    ('access', factories.AccessFactory, False),
    ('cohort', factories.CohortFactory, True),
    ('contact', factories.ContactFactory, True),
    ('partner', factories.PartnerFactory, True),
    ('partnerrole', factories.PartnerRoleFactory, False),
    ('contract', factories.ContractFactory, True),
    ('contacttype', factories.ContactTypeFactory, False),
    ('datatype', factories.DataTypeFactory, False),
    #('datadeclaration', factories.DataDeclarationFactory, True),
    ('dataset', factories.DatasetFactory, True),
    #('document', factories.DocumentFactory, True),
    #('documenttype', factories.DocumentTypeFactory, True),
    #('fundingsource', factories.FundingSourceFactory, True),
    ('project', factories.ProjectFactory, True),
    #('publication', factories.PublicationFactory, True),
    #('share', factories.ShareFactory, True),
    #('legalbasis', factories.LegalBasisFactory, True),
    #('legalbasistype', factories.LegalBasisTypeFactory, True),
    #('personaldatatype', factories.PersonalDataTypeFactory, True),
    #('datalocation', factories.DataLocationFactory, True),
    #('storageresource', factories.StorageResourceFactory, True),
    #('sensitivityclass', factories.SensitivityClassFactory, True),
    #('restrictionclass', factories.RestrictionClassFactory, True),
    #('userestriction', factories.UseRestrictionFactory, True),
    #('studyterm', factories.StudyTermFactory, True),
    #('geneterm', factories.GeneTermFactory, True),
    #('phenotypeterm', factories.PhenotypeTermFactory, True),
    #('diseaseterm', factories.DiseaseTermFactory, True),
    #('user', factories.UserFactory, True),
)
## TODO GENERATE AND FIX ALL COMMENTED MODELS


@pytest.mark.parametrize('model,factory,expected', MODELS)
def test_detail_url_for_models(model, factory, expected):
    instance = factory.create()
    assert (instance.get_detail_url() is not None) is expected