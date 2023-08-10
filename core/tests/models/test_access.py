from auditlog.models import LogEntry
from core.models.access import StatusChoices, Access
from datetime import date, timedelta
from test.factories import AccessFactory


def test_expire_accesses():
    """
    Tests that `expire_accesses` method correctly terminates Access with an expiration
    date previous to the given date and that this creates a LogEntry in the db
    """
    dates = [
        date.today() - timedelta(days=15),
        date.today() - timedelta(days=365),
        date.today() - timedelta(days=1),
        date.today(),
        date.today() + timedelta(days=1),
    ]
    accesses = [
        AccessFactory(status=StatusChoices.active, grant_expires_on=dates[i])
        for i in range(5)
    ]

    Access.expire_accesses(date.today())

    for access in accesses:
        access.refresh_from_db()
        if access.status == StatusChoices.terminated:
            assert "Automatically terminated" in access.access_notes
            logs = LogEntry.objects.get_for_object(access)
            assert len(logs) == 2

            last_log = logs.order_by("-timestamp").first()
            assert last_log.action == LogEntry.Action.UPDATE
            assert "status" in last_log.changes
            assert "access_notes" in last_log.changes

    assert accesses[0].status == StatusChoices.terminated
    assert accesses[1].status == StatusChoices.terminated
    assert accesses[2].status == StatusChoices.terminated
    assert accesses[3].status == StatusChoices.active
    assert accesses[4].status == StatusChoices.active
