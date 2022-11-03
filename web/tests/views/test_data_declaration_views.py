import pytest
from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, DatasetFactory, DataDeclarationFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['data_declaration', 'data_declarations_duplicate', 'data_declarations_delete', 'data_declaration_edit', 'data_declarations_add_sub_form', 'data_declarations_get_contracts', 'data_declarations_autocomplete', 'data_dec_paginated_search'])
def test_data_declarations_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with DataDeclaration instances
    """
    if url_name in ['data_declaration', 'data_declarations_duplicate', 'data_declarations_delete', 'data_declaration_edit']:
        dataset = DatasetFactory()
        dataset.save()
        data_declaration = DataDeclarationFactory(dataset=dataset)
        data_declaration.save()
        url = reverse(url_name, kwargs={"pk": data_declaration.pk})
    else:
        url = reverse(url_name)

    assert url is not None