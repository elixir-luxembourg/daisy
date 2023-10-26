from django.shortcuts import reverse

from notification.models import Notification


def test_api_get_notifications(client, user_normal, notifications_for_user):
    """
    Test that the api returns the correct number of notifications for a given user

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 5
    notifications = notifications_for_user(user_normal, expected_number)
    assert client.login(
        username=user_normal.username, password="password"
    ), "Login failed"

    json_response = client.get(reverse("api_notifications"))
    assert json_response.status_code == 200
    data = json_response.json()["data"]
    assert len(data) == expected_number
    received_ids = [n["id"] for n in data]
    for notification in notifications:
        assert notification.to_json()["id"] in received_ids


def test_api_get_notifications_wrong_user(
    client, user_normal, user_staff, notifications_for_user
):
    """
    Test that the api returns no notifications for a user that is not the recipient

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 5
    notifications_for_user(user_normal, expected_number)
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.get(reverse("api_notifications"))
    assert json_response.status_code == 200
    assert json_response.json()["data"] == []


def test_api_get_notifications_admin(
    client, user_normal, user_staff, notifications_for_user
):
    """
    Test that the option `as_admin` returns all notifications

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 5
    notifications = notifications_for_user(user_normal, expected_number)
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.get(reverse("api_notifications"), {"as_admin": "true"})
    assert json_response.status_code == 200
    data = json_response.json()["data"]
    assert len(data) == expected_number
    received_ids = [n["id"] for n in data]
    for notification in notifications:
        assert notification.to_json()["id"] in received_ids


def test_dismiss_notification(client, user_normal, notifications_for_user):
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
    assert json_response.status_code == 200
    data = json_response.json()["data"]
    assert len(data) == expected_number
    assert data[0]["id"] == notification.pk
    notification = Notification.objects.get(pk=notification.pk)

    assert notification.dismissed


def test_dismiss_notification_wrong_user(
    client, user_normal, user_staff, notifications_for_user
):
    """
    Test that a notification is not dismissed if the user is not the recipient

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param user_staff: User fixture with staff permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 1
    notification = notifications_for_user(user_normal, expected_number)[0]
    assert client.login(
        username=user_staff.username, password="password"
    ), "Login failed"

    json_response = client.patch(reverse("api_dismiss", args=[notification.pk]))
    assert json_response.status_code == 403
    notification = Notification.objects.get(pk=notification.pk)

    assert not notification.dismissed


def test_dismiss_all_notifications(client, user_normal, notifications_for_user):
    """
    Test all notifications for a given content type are correctly dismissed

    :param client: Django test client
    :param user_normal: User fixture with normal permissions
    :param notifications_for_user: Fixture to create notifications for a given user
    """
    expected_number = 5
    notifications_for_user(user_normal, expected_number, user_normal)

    assert client.login(
        username=user_normal.username, password="password"
    ), "Login failed"
    json_response = client.patch(
        reverse("api_dismiss_all", args=[user_normal.__class__.__name__.lower()])
    )
    assert json_response.status_code == 200
    notifications = Notification.objects.filter(recipient=user_normal)
    for notif in notifications:
        assert notif.dismissed
