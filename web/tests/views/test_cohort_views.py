import pytest

from django.shortcuts import reverse
from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, CohortFactory


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name',
    [
        'cohorts',
        'cohort_add',
        'cohorts_export',
        'cohort',
        'cohort_delete',
        'cohort_edit',
        'cohort_publish',
        'cohort_unpublish'
    ],
)
def test_cohorts_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access the urls associated with Cohort instances
    """
    if url_name in ['cohorts', 'cohort_add', 'cohorts_export']:
        url = reverse(url_name)
    else:
        cohort = CohortFactory()
        cohort.save()
        url = reverse(url_name, kwargs={'pk': cohort.pk})

    assert url is not None
