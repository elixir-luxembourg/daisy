import pytest

from typing import Optional
from django.shortcuts import reverse
from django.test.client import Client

from test.factories import VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup, CohortFactory, UserFactory
from core.models.user import User
from core.models.cohort import Cohort
from core.constants import Permissions
from .utils import check_response_status, check_datasteward_restricted_url


def check_cohort_view_permissions(url: str, user: User, action: Optional[Permissions], cohort: Optional[Cohort] = None):
    # For now, anyone can create or edit the cohorts. However, only data stewards should be able to delete them
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
        # Anyone can edit Cohort instances
        check_response_status(url, user, [], obj=cohort)

    else:
        # If other Permissions are needed, add the expected behavior
        raise ValueError(f"Unexpected permission {action} asked to work on Cohort instance")


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize(
    'url_name, perm',
    [
        ('cohorts', None),
        ('cohort_add', None),
        ('cohort', None),
        ('cohort_delete', Permissions.DELETE),
        ('cohort_edit', Permissions.EDIT),
    ],
)
def test_cohorts_views_permissions(permissions, group, url_name, perm):
    """
    Tests whether users from different groups can access the urls associated with Cohort instances
    """
    cohort = None
    if url_name in ['cohorts', 'cohort_add']:
        url = reverse(url_name)
    else:
        cohort = CohortFactory()
        cohort.save()
        url = reverse(url_name, kwargs={'pk': cohort.pk})

    assert url is not None
    user = UserFactory(groups=[group()])
    check_cohort_view_permissions(url, user, perm, cohort)


@pytest.mark.parametrize('group', [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup])
@pytest.mark.parametrize('url_name', ['cohort_publish', 'cohort_unpublish', 'cohorts_export'])
def test_cohorts_publications_and_export(permissions, group, url_name):
    user = UserFactory(groups=[group()])
    kwargs = {}
    if url_name != 'cohorts_export':
        cohort = CohortFactory()
        kwargs.update({'pk': cohort.pk})

    url = reverse(url_name, kwargs=kwargs)
    check_datasteward_restricted_url(url, user)
