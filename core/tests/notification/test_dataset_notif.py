import datetime
from datetime import timedelta

import pytest

from test.factories import DatasetFactory, UserFactory, DataDeclarationFactory
from core.models import Dataset
from notification.models import Notification, NotificationSetting


@pytest.mark.parametrize("event", ["embargo_date", "end_of_storage_duration"])
@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
@pytest.mark.django_db
def test_dataset_notification_creation(event, offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    user = UserFactory(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=offset)
    notif_setting.save()

    dataset = DatasetFactory(title="Test dataset", local_custodians=[user])
    data_declaration = DataDeclarationFactory(dataset=dataset)
    setattr(data_declaration, event, event_date)
    data_declaration.save()

    assert Notification.objects.count() == 0
    Dataset.make_notifications(today)
    assert Notification.objects.count() == 1
