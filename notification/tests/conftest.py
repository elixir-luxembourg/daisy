import pytest
from typing import TYPE_CHECKING
from notification.models import Notification, NotificationVerb

if TYPE_CHECKING:
    from django.conf import settings
    from django.db.models import Model


@pytest.fixture
def notifications_for_user():
    """
    Fixture that builds a method to create notifications for a given user

    :return: a method to create notifications for a given user
    """

    def _method(
        user: "settings.AUTH_USER_MODEL",
        number: int = 10,
        content_object: "Model" = None,
    ):
        """
        Create notifications for a given user

        :param user: The user to create notifications for
        :param number: The number of notifications to create
        :param content_object: The content object to attach to the notifications
        :return: The list of created notifications
        """
        if content_object is None:
            content_object = user
        for i in range(number):
            Notification.objects.create(
                recipient=user,
                verb=i % 2 == 0 and NotificationVerb.start or NotificationVerb.end,
                content_object=content_object,  # should be a dataset but not tested yet
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
