from core.models import Dataset, Access
from core.utils import DaisyLogger

from django.shortcuts import reverse
from web.tests.views.utils import login_test_user

import datetime
import pytest

log = DaisyLogger(__name__)


@pytest.mark.parametrize("is_steward", [True, False])
def test_access_history(client, is_steward, user_vip, user_data_steward):
    new_dataset = Dataset(title="First test dataset")
    new_dataset.save()
    new_dataset.local_custodians.set([user_vip])
    new_dataset.save()

    new_access = Access(dataset=new_dataset, created_by=user_vip)
    new_access.grant_expires_on = datetime.date.today() + datetime.timedelta(days=1)
    new_access.save()

    new_access.was_generated_automatically = not new_access.was_generated_automatically
    new_access.save()

    another_dataset = Dataset(title="Second test dataset")
    another_dataset.save()
    another_access = Access(dataset=another_dataset, created_by=user_data_steward)
    another_access.save()

    if is_steward:
        login_test_user(client, user_data_steward)
        res = client.get(reverse("history"), follow=True)
        assert res.status_code == 200
        assert len(res.context["object_list"]) == 3

        res = client.get(
            reverse("history"), {"entity_name": "access", "entity_attr": "id"}
        )
        assert res.status_code == 200
        assert len(res.context["object_list"]) == 2

    else:
        login_test_user(client, user_vip)
        res = client.get(reverse("history"), follow=True)
        assert res.status_code == 403

        res = client.get(
            reverse("history"), {"entity_name": "access", "entity_id": new_access.pk}
        )
        assert res.status_code == 200
        assert len(res.context["object_list"]) == 2
