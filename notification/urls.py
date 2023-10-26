from django.urls import path
from notification.views import (
    NotificationAdminView,
    NotificationsListView,
    NotificationSettingEditView,
)
from notification.api import (
    api_dismiss_notification,
    api_dismiss_all_notifications,
    api_get_notifications,
    api_get_notifications_number,
)

notif_urls = [
    # Notifications
    path(
        "",
        NotificationsListView.as_view(),
        name="notifications",
    ),
    path(
        "admin",
        NotificationAdminView.as_view(),
        name="notifications_admin",
    ),
    path(
        "admin/<int:pk>",
        NotificationAdminView.as_view(),
        name="notifications_admin_for_user",
    ),
    path(
        "settings",
        NotificationSettingEditView.as_view(),
        name="notifications_settings",
    ),
    # API
    path("api/notifications", api_get_notifications, name="api_notifications"),
    path("api/dismiss/<int:pk>", api_dismiss_notification, name="api_dismiss"),
    path(
        "api/dismiss-all/<str:object_type>",
        api_dismiss_all_notifications,
        name="api_dismiss_all",
    ),
    path(
        "api/notifications-number",
        api_get_notifications_number,
        name="api_notif_number",
    ),
]
