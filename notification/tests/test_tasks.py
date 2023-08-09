import pytest
from django.utils import timezone
from faker import Faker

from notification import tasks
from notification.models import NotificationStyle, NotificationSetting
from test.factories import *

fake = Faker()
TZ = settings.TZINFO

notifications_periods = [
    ("-90d", "-60d"),  # 2/3 months ago
    ("-90d", "-60d"),
    ("-20d", "-10d"),  # 20/2 days ago
    ("-7d", "-6d"),
    ("-7h", "-2h"),  # 7/2 hours ago
    ("-10s", "-1s"),  # 10s/1s ago ...
    ("-10s", "-1s"),
]


notifications_periods_with_notification_style = [
    ("once_per_day", notifications_periods, 3),
    ("once_per_week", notifications_periods, 4),
    ("once_per_month", notifications_periods, 5),
]


@pytest.mark.parametrize(
    "period,start_ends,expected", notifications_periods_with_notification_style
)
def test_no_notification_style(
    celery_session_worker, user_normal, period, start_ends, expected
):
    """
    No notification report should hit as no notification style is set
    """
    dataset = DatasetFactory()
    now = timezone.now()
    notifications = [
        DatasetNotificationFactory(actor=user_normal) for start, end in start_ends
    ]
    # set use to the notif style
    user_normal.save()
    users = tasks.send_notifications(period)
    assert len(users) == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "period,start_ends,expected", notifications_periods_with_notification_style
)
def test_send_notifications(
    celery_session_worker, user_normal, period, start_ends, expected
):
    """
    Test notification report
    """
    # create notification style
    ns = NotificationSetting(user=user_normal, style=NotificationStyle[period])
    ns.save()
    # create test data
    DatasetFactory()
    for start, end in start_ends:
        n = DatasetNotificationFactory(actor=user_normal)
        n.time = fake.date_time_between(start_date=start, end_date=end, tzinfo=TZ)
        n.save()

    # set times as we do in tasks module
    now = timezone.now()
    time = now - tasks.NOTIFICATION_MAPPING[NotificationStyle[period]]
    users = tasks.send_notifications(period)

    assert len(users) == 1
    assert len(users[0].notifications.all()) == len(notifications_periods)
    assert len(users[0].notifications.filter(time__gte=time)) == expected
