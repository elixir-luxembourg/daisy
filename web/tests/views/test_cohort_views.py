import pytest

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, CohortFactory, UserFactory
from django.shortcuts import reverse

from .utils import check_response_status


def check_cohort_view_permissions(url, user, cohort):
    if cohort is not None:
        assert user.has_permission_on_object('core.edit_cohort', cohort)

        if user.is_part_of(DataStewardGroup):
            assert user.has_permission_on_object('core.delete_cohort', cohort)
        else:
            assert not user.has_permission_on_object('core.delete_cohort', cohort)
    else:
        assert user.has_perm('core.add_cohort')

    if url == 'cohort_add':
        check_response_status(url, user, 'core.add_cohort')

    elif url == 'cohort_delete':
        check_response_status(url, user, 'core.delete_cohort', obj=cohort)

    elif url in ['cohorts', 'cohort']:
        check_response_status(url, user, 'core.view_cohort')

    else:
        check_response_status(url, user, 'core.edit_cohort', obj=cohort)


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
    # For now, anyone can create or edit the cohorts. However, only data stewards should be able to delete them
    # FIXME
    #  Discuss the correct permissions to be given
    cohort = None
    if url_name in ['cohorts', 'cohort_add', 'cohorts_export']:
        url = reverse(url_name)
    else:
        cohort = CohortFactory()
        cohort.save()
        url = reverse(url_name, kwargs={'pk': cohort.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_cohort_view_permissions(url, user, cohort)
