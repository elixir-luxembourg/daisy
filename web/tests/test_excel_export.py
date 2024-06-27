import pytest
from test import factories

from django.urls import reverse


@pytest.mark.parametrize(
    "url_name,factory",
    [
        ("datasets_export", factories.DatasetFactory),
        ("projects_export", factories.ProjectFactory),
        ("contracts_export", factories.ContractFactory),
        ("partners_export", factories.PartnerFactory),
        ("cohorts_export", factories.CohortFactory),
    ],
)
def test_excel_export(permissions, client_user_data_steward, url_name, factory):
    """
    Test view for exporting records to Excel file.
    """

    number_of_objects = 4
    objects = factory.create_batch(number_of_objects)
    url = reverse(url_name)
    response = client_user_data_steward.get(url)

    assert response.status_code == 200

    # TODO: verify the records are correct - and number of records matches
    # with io.BytesIO(response.content) as fh:
    #    pass
    #    df = pd.io.excel.read_excel(fh, sheetname=0)
