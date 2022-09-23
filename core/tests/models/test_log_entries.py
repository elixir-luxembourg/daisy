import datetime

from core.models.access import Access
from core.models.dataset import Dataset

from auditlog.models import LogEntry

def test_access_logentries():
    new_dataset = Dataset()
    new_dataset.save()
    new_access = Access(dataset=new_dataset)
    new_access.save()
    assert LogEntry.objects.count() == 1

    new_access.grant_expires_on = datetime.date.today() + datetime.timedelta(days=1)
    new_access.save()
    assert LogEntry.objects.count() == 2

    new_access.delete()
    assert LogEntry.objects.count() == 3


