import pytest

from test.factories import DatasetFactory, DatasetNotificationFactory


@pytest.mark.parametrize(
    "factory, object_factory", [(DatasetNotificationFactory, DatasetFactory)]
)
def test_notification_urls(user_normal, factory, object_factory):
    notification = factory(recipient=user_normal, content_object=object_factory())
    assert (
        notification.get_absolute_url()
        == notification.content_object.get_absolute_url()
    )
