import pytest

from notification.models import Notification, NotificationVerb


# notifications fixtures
@pytest.fixture
def notifications_for_user():
    def _method(user, number=10, content_type=None):
        if content_type is None:
            content_type = user
        for i in range(number):
            Notification.objects.create(
                recipient=user,
                verb=i % 2 == 0 and NotificationVerb.start or NotificationVerb.end,
                content_object=content_type,  # should be a dataset but not tested yet
            )
        return Notification.objects.all()

    return _method


@pytest.fixture
def user_normal(django_user_model):
    user = django_user_model.objects.create_user(
        username="john.doe", password="password", email="john.doe@email.com"
    )
    return user


@pytest.fixture
def user_staff(django_user_model):
    user = django_user_model.objects.create_user(
        username="admin.doe", password="password", email="admin.doe@email.com"
    )
    user.is_staff = True
    user.save()
    return user
