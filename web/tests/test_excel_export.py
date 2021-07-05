import pytest
from test import factories


from django.urls import reverse

@pytest.mark.skip(reason="TBD")
@pytest.mark.parametrize('url_name,factory,model', [
    ('datasets_export', factories.DatasetFactory, 'Dataset'),
    ('projects_export', factories.ProjectFactory, 'Project'),
    ('contracts_export', factories.ContractFactory, 'Contract'),
    ('partners_export', factories.PartnerFactory, 'Partner'),
    ('cohorts_export', factories.CohortFactory, 'Cohort'),
])
def test_excel_export(client_user_vip,  url_name, factory, model):
    """
    Test view for exporting records to Excel file.
    """
    
    # TODO: The database is probably empty at the moment

    url = reverse(url_name)
    response = client_user_vip.get(url)
    assert response.status_code == 200
