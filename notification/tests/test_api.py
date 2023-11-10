from typing import TYPE_CHECKING
from django.shortcuts import reverse

from notification.models import Notification

if TYPE_CHECKING:
    from django.conf import settings
    from django.test import Client
    from django.http import JsonResponse


def is_valid_api_response(
    response: "JsonResponse", expected_content_length: int
) -> list:
    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    data = response.json()["data"]
    assert len(data) == expected_content_length
    return data


def test_api_get_notifications(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test that the api returns the correct number of notifications for a given user

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    notifications = notifications_for_user(user_normal)
    assert client.login(
        username=user_normal.username, password="password"
    ), "Login failed"
    json_response = client.get(reverse("api_notifications"))
    data = is_valid_api_response(json_response, len(notifications))
    received_ids = [n["id"] for n in data]
    for notification in notifications:
        assert notification.to_json()["id"] in received_ids


def test_api_get_notifications_wrong_user(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    user_staff: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test that the api returns no notifications for a user that is not the recipient

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    notifications_for_user(user_normal)
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.get(reverse("api_notifications"))
    is_valid_api_response(json_response, 0)


def test_api_get_notifications_admin_with_recipient(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    user_staff: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """

    :param client:
    :param user_normal:
    :param user_staff:
    :param notifications_for_user:
    :return:
    """
    notifications = notifications_for_user(user_normal)
    unwanted_notifications = notifications_for_user(user_staff)

    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.get(
        reverse("api_notifications"), {"as_admin": "true", "recipient": user_normal.pk}
    )
    data = is_valid_api_response(json_response, len(notifications))
    received_ids = [n["id"] for n in data]
    for notification in unwanted_notifications:
        assert notification.to_json()["id"] not in received_ids


def test_api_get_notifications_admin(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    user_staff: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test that the option `as_admin` returns all notifications

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    notifications = notifications_for_user(user_normal)
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.get(reverse("api_notifications"), {"as_admin": "true"})
    data = is_valid_api_response(json_response, len(notifications))
    received_ids = [n["id"] for n in data]
    for notification in notifications:
        assert notification.to_json()["id"] in received_ids


def test_dismiss_notification(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test that a notification is correctly dismissed after calling the api

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 1
    notification = notifications_for_user(user_normal, expected_number)[0]
    assert client.login(
        username=user_normal.username, password="password"
    ), "Login failed"

    json_response = client.patch(reverse("api_dismiss", args=[notification.pk]))
    data = is_valid_api_response(json_response, expected_number)
    assert data[0]["id"] == notification.pk
    notification = Notification.objects.get(pk=notification.pk)

    assert notification.dismissed


def test_dismiss_notification_wrong_user(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    user_staff: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test that a notification is not dismissed if the user is not the recipient

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    notification = notifications_for_user(user_normal)[0]
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.patch(reverse("api_dismiss", args=[notification.pk]))
    assert json_response.status_code == 403
    notification = Notification.objects.get(pk=notification.pk)

    assert not notification.dismissed


def test_dismiss_all_notifications(
    client: "Client",
    user_normal: "settings.AUTH_USER_MODEL",
    notifications_for_user: callable,
):
    """
    Test all notifications for a given content type are correctly dismissed

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    notifications = notifications_for_user(user_normal)

    assert client.login(
        username=user_normal.username, password="password"
    ), "Login failed"
    json_response = client.patch(
        reverse("api_dismiss_all", args=[user_normal.__class__.__name__.lower()])
    )
    is_valid_api_response(json_response, len(notifications))

    notifications = Notification.objects.filter(recipient=user_normal)
    for notif in notifications:
        assert notif.dismissed
