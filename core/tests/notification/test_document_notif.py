import datetime
from datetime import timedelta

import pytest

from test.factories import (
    ProjectDocumentFactory,
    ContractDocumentFactory,
    ContractFactory,
    UserFactory,
    ProjectFactory,
)
from core.models import Document
from notification.models import Notification, NotificationSetting


@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
@pytest.mark.django_db
def test_document_notification_creation(offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=offset)
    notif_setting.save()

    project = ProjectFactory.create(title="Test project", local_custodians=[user])
    _ = ProjectDocumentFactory.create(content_object=project, expiry_date=event_date)

    contract = ContractFactory.create(local_custodians=[user])
    _ = ContractDocumentFactory.create(content_object=contract, expiry_date=event_date)

    assert Notification.objects.count() == 0
    Document.make_notifications(today)
    assert Notification.objects.count() == 2


def test_document_unmatching_dates():
    today = datetime.date.today()
    event_date = today + timedelta(days=10)

    user = UserFactory.create(email="lc@uni.lu")
    notif_setting = NotificationSetting(user=user, notification_offset=30)
    notif_setting.save()

    project = ProjectFactory.create(title="Test project", local_custodians=[user])
    _ = ProjectDocumentFactory.create(content_object=project, expiry_date=event_date)

    contract = ContractFactory.create(local_custodians=[user])
    _ = ContractDocumentFactory.create(content_object=contract, expiry_date=event_date)

    assert Notification.objects.count() == 0
    Document.make_notifications(today)
    assert Notification.objects.count() == 0


@pytest.mark.parametrize("offset", [1, 10, 30, 60, 90])
def test_document_project_lc_notification(offset):
    today = datetime.date.today()
    event_date = today + timedelta(days=offset)

    contract_lc = UserFactory.create(email="contract_lc@uni.lu")
    setting1 = NotificationSetting(user=contract_lc, notification_offset=offset)
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
    contract = ContractFactory.create(
        project=project, local_custodians=[contract_lc, p1_lc]
    )

    _ = ContractDocumentFactory.create(content_object=contract, expiry_date=event_date)

    assert Notification.objects.count() == 0
    Document.make_notifications(today)
    assert len(Notification.objects.filter(recipient=contract_lc)) == 1
    assert len(Notification.objects.filter(recipient=p1_lc)) == 1
    assert len(Notification.objects.filter(recipient=p2_lc)) == 1


def test_document_handles_no_recipients():
    exec_date = datetime.date.today()
    Document.make_notifications(exec_date)
    assert Notification.objects.count() == 0
