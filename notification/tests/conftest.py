import pytest

from notification.models import Notification, NotificationVerb

# notifications fixtures
@pytest.fixture
def notifications(user_lambda):
    for i in range(10):
        Notification.objects.create(
            actor=user_lambda,
            verb=i%2==0 and NotificationVerb.new_dataset or NotificationVerb.update_dataset,
            content_object=user_lambda # should be a dataset but not tested yet
        )
    yield Notification.objects.all()