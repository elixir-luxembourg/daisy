from datetime import datetime, timedelta

import pytest

from notification import tasks
from notification.models import NotificationSetting, Notification, NotificationVerb
from test.factories import DatasetFactory
from django.test import override_settings


@pytest.mark.django_db
@override_settings(NOTIFICATIONS_DISABLED=False)
def test_send_notifications_for_user_upcoming_events_today(user_normal):
    """
    Test notification report processing for today's notifications
    """
    # Enable user notification setting send_email
    ns = NotificationSetting(user=user_normal, send_email=True)
    ns.save()
    n = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n.save()

    notifications_not_processed = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_not_processed) == 1

    # send notifications
    tasks.send_notifications_for_user_upcoming_events(only_one_day=True)

    notifications_after_sending = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_after_sending) == 0


@pytest.mark.django_db
@override_settings(NOTIFICATIONS_DISABLED=False)
def test_send_notifications_for_user_upcoming_events_execution_date(user_normal):
    """
    Test notification report processing for execution date notifications and previous days
    """
    # Enable user notification setting send_email
    ns = NotificationSetting(user=user_normal, send_email=True)
    ns.save()

    n = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n.save()

    yesterday = datetime.now() - timedelta(days=1)

    n2 = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n2.save()
    # Force change of n2 time
    Notification.objects.filter(pk=n2.pk).update(time=yesterday)

    earlier_date = datetime.now() - timedelta(days=3)

    n3 = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n3.save()
    # Force change of n3 time
    Notification.objects.filter(pk=n3.pk).update(time=earlier_date)

    notifications_not_processed = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_not_processed) == 3

    # send notifications
    tasks.send_notifications_for_user_upcoming_events(
        yesterday.date().strftime("%Y-%m-%d")
    )

    notifications_after_sending = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_after_sending) == 1


@pytest.mark.django_db
@override_settings(NOTIFICATIONS_DISABLED=False)
def test_send_notifications_for_user_upcoming_events_only_one_day(user_normal):
    """
    Test notification report processing for execution date notifications only
    """
    # Enable user notification setting send_email
    ns = NotificationSetting(user=user_normal, send_email=True)
    ns.save()

    n = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n.save()

    yesterday = datetime.now() - timedelta(days=1)

    n2 = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n2.save()
    # Force change of n2 time
    Notification.objects.filter(pk=n2.pk).update(time=yesterday)

    earlier_date = datetime.now() - timedelta(days=3)

    n3 = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n3.save()
    # Force change of n3 time
    Notification.objects.filter(pk=n3.pk).update(time=earlier_date)

    notifications_not_processed = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_not_processed) == 3

    # send notifications
    tasks.send_notifications_for_user_upcoming_events(
        yesterday.date().strftime("%Y-%m-%d"), only_one_day=True
    )

    notifications_after_sending = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_after_sending) == 2


@pytest.mark.django_db
@override_settings(NOTIFICATIONS_DISABLED=False)
def test_send_all_notifications_for_user_upcoming_events(user_normal):
    """
    Test notification report processing for all missed notifications
    """
    # Enable user notification setting send_email
    ns = NotificationSetting(user=user_normal, send_email=True)
    ns.save()
    n = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n.save()
    n2 = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n2.save()
    Notification.objects.filter(pk=n2.pk).update(
        time=datetime.now() - timedelta(days=1)
    )

    notifications_not_processed = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_not_processed) == 2

    # send notifications
    tasks.send_notifications_for_user_upcoming_events()

    notifications_after_sending = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_after_sending) == 0


@pytest.mark.django_db
@override_settings(NOTIFICATIONS_DISABLED=True)
def test_send_no_notifications(user_normal):
    """
    Test notification report sending disabled
    """
    # Enable user notification setting send_email
    ns = NotificationSetting(user=user_normal, send_email=True)
    ns.save()
    n = Notification(
        recipient=user_normal,
        content_object=DatasetFactory(),
        dispatch_by_email=True,
        verb=NotificationVerb.expire,
    )
    n.save()

    notifications_not_processed = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_not_processed) == 1

    # send notifications
    tasks.send_notifications_for_user_upcoming_events()

    notifications_after_sending = Notification.objects.filter(
        recipient=user_normal.id, dispatch_by_email=True, processing_date=None
    )
    assert len(notifications_after_sending) == 1
