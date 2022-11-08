import pytest

from typing import Optional
from django.shortcuts import reverse

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, CohortFactory, UserFactory
from core.models.user import User
from core.models.cohort import Cohort
from core.constants import Permissions
from .utils import check_response_status


def check_cohort_view_permissions(url: str, user: User, action: Optional[Permissions], cohort: Optional[Cohort] = None):
    # For now, anyone can create or edit the cohorts. However, only data stewards should be able to delete them
    # FIXME
    #  Discuss the correct permissions to be given
    if action == Permissions.DELETE:
        # Only data stewards can delete Cohort instances
        if user.is_part_of(DataStewardGroup()):
            assert user.has_permission_on_object(f'core.{action.value}_cohort', cohort)
        else:
            assert not user.has_permission_on_object(f'core.{action.value}_cohort', cohort)

        check_response_status(url, user, [f'core.{action.value}_cohort'], obj=cohort)

    elif action is None:
        # Everyone can view or create anything, so no permission was designed for it
        check_response_status(url, user, [], obj=cohort)

    elif action == Permissions.EDIT:
        # FIXME: Anyone can edit Cohort instances
        check_response_status(url, user, [], obj=cohort)

    else:
        # If other Permissions are needed, add the expected behavior
        raise ValueError(f"Unexpected permission {action} asked to work on Cohort instance")


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'destination_tuple',
    [
        ('cohorts', None),
        ('cohort_add', None),
        ('cohorts_export', None),
        ('cohort', None),
        ('cohort_delete', Permissions.DELETE),
        ('cohort_edit', Permissions.EDIT),
        # FIXME: These two must be checked, but who is staff?
        # 'cohort_publish',
        # 'cohort_unpublish'
    ],
)
def test_cohorts_views_permissions(permissions, group, destination_tuple):
    """
    Tests whether users from different groups can access the urls associated with Cohort instances
    """
    url_name, action = destination_tuple
    cohort = None
    if url_name in ['cohorts', 'cohort_add', 'cohorts_export']:
        url = reverse(url_name)
    else:
        cohort = CohortFactory()
        cohort.save()
        url = reverse(url_name, kwargs={'pk': cohort.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_cohort_view_permissions(url, user, action, cohort)
