import datetime
from datetime import timedelta

import pytest

from test.factories import DatasetFactory, UserFactory, ProjectFactory, AccessFactory
from core.models import Access
from core.models.access import StatusChoices
from notification.models import Notification, NotificationSetting


@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
@pytest.mark.django_db
def test_access_success_notification_creation(offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=offset)
    notif_setting.save()

    dataset = DatasetFactory.create(title="Test dataset", local_custodians=[user])
    _ = AccessFactory.create(
        dataset=dataset, grant_expires_on=event_date, status=StatusChoices.active
    )

    assert Notification.objects.count() == 0
    Access.make_notifications(today)
    assert Notification.objects.count() == 1


def test_accesss_unmatching_dates():
    today = datetime.date.today()
    event_date = today + timedelta(days=20)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=30)
    notif_setting.save()

    dataset = DatasetFactory.create(title="Test dataset", local_custodians=[user])
    _ = AccessFactory.create(
        dataset=dataset, grant_expires_on=event_date, status=StatusChoices.active
    )

    assert Notification.objects.count() == 0
    Access.make_notifications(today)
    assert Notification.objects.count() == 0


@pytest.mark.parametrize(
    "state",
    [StatusChoices.precreated, StatusChoices.suspended, StatusChoices.terminated],
)
@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
def test_access_no_notif_inactive_access(state, offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=offset)
    notif_setting.save()

    dataset = DatasetFactory.create(title="Test dataset", local_custodians=[user])
    _ = AccessFactory.create(dataset=dataset, grant_expires_on=event_date, status=state)

    assert Notification.objects.count() == 0
    Access.make_notifications(today)
    assert Notification.objects.count() == 0


@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
def test_access_project_lc_notification(offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    dataset_lc = UserFactory.create(email="dataset_lc@uni.lu")
    setting1 = NotificationSetting(user=dataset_lc, notification_offset=offset)
    setting1.save()

    p1_lc = UserFactory.create(email="p1_lc@uni.lu")
    setting2 = NotificationSetting(user=p1_lc, notification_offset=offset)
    setting2.save()

    p2_lc = UserFactory.create(email="p2_lc@uni.lu")
    setting3 = NotificationSetting(user=p2_lc, notification_offset=offset)
    setting3.save()

    project = ProjectFactory.create(
        title="Test project", local_custodians=[p1_lc, p2_lc]
    )
    dataset = DatasetFactory.create(
        title="Test dataset", project=project, local_custodians=[dataset_lc, p1_lc]
    )
    _ = AccessFactory.create(
        dataset=dataset, grant_expires_on=event_date, status=StatusChoices.active
    )

    assert Notification.objects.count() == 0
    Access.make_notifications(today)
    assert len(Notification.objects.filter(recipient=dataset_lc)) == 1
    assert len(Notification.objects.filter(recipient=p1_lc)) == 1
    assert len(Notification.objects.filter(recipient=p2_lc)) == 1


def test_access_handles_no_recipients():
    exec_date = datetime.date.today()
    Access.make_notifications(exec_date)
    assert Notification.objects.count() == 0
