from core.models import Dataset, Access
from django.shortcuts import reverse

import datetime
import pytest


@pytest.mark.parametrize("is_admin", [True, False])
def test_access_history(client, is_admin, user_admin, user_normal):

    new_dataset = Dataset()
    new_dataset.save()

    new_access = Access(dataset=new_dataset, created_by=user_normal)
    new_access.grant_expires_on = datetime.date.today() + datetime.timedelta(days=1)
    new_access.save()

    new_access.was_generated_automatically = False
    new_access.save()

    res = client.get(reverse('history'), follow=True)
    assert res.status_code == 200
    # Make a bunch of logs at different dates, etc.
    # Test the query filters
