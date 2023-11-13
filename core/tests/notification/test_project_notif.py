import datetime
from datetime import timedelta

import pytest

from test.factories import (
    UserFactory,
    ProjectFactory,
)
from core.models import Project
from notification.models import Notification, NotificationSetting


@pytest.mark.parametrize("event", ["start_date", "end_date"])
@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
@pytest.mark.django_db
def test_project_notification_creation(event, offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=offset)
    notif_setting.save()

    project = ProjectFactory.create(title="Test project", local_custodians=[user])
    setattr(project, event, event_date)
    project.save()

    assert Notification.objects.count() == 0
    Project.make_notifications(today)
    assert Notification.objects.count() == 1


@pytest.mark.parametrize("event", ["start_date", "end_date"])
def test_project_unmatching_dates(event):
    today = datetime.date.today()
    event_date = today + timedelta(days=20)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=30)
    notif_setting.save()

    project = ProjectFactory.create(title="Test project", local_custodians=[user])
    setattr(project, event, event_date)
    project.save()

    assert Notification.objects.count() == 0
    Project.make_notifications(today)
    assert Notification.objects.count() == 0


def test_project_handles_no_recipients():
    exec_date = datetime.date.today()
    Project.make_notifications(exec_date)
    assert Notification.objects.count() == 0
