from abc import ABC, abstractmethod
import typing
from typing import List, Optional
from datetime import timedelta

if typing.TYPE_CHECKING:
    from django.conf import settings
    from datetime import date
    from notification.models import NotificationVerb

    User = settings.AUTH_USER_MODEL


class NotifyMixin(ABC):
    @staticmethod
    @abstractmethod
    def get_notification_recipients() -> List["User"]:
        """
        Should query the users based on their notification settings
        and the entity.
        """
        pass

    @classmethod
    def make_notifications(cls, exec_date: "date"):
        """
        Creates notifications for the reciepients based on
        the business logic of the entity.

        Params:
            exec_date: The date of execution of the task.
        """
        recipients = cls.get_notification_recipients()
        for user in recipients:
            notification_setting = cls.get_notification_setting(user)
            if not (
                notification_setting.send_email or notification_setting.send_in_app
            ):
                continue
            day_offset = timedelta(days=notification_setting.notification_offset)
            cls.make_notifications_for_user(day_offset, exec_date, user)

    @classmethod
    @abstractmethod
    def make_notifications_for_user(
        cls, day_offset: "timedelta", exec_date: "date", user: "User"
    ):
        """
        Creates notifications for the user based on the business logic of the entity.

        Params:
            day_offset: The offset of the notification.
            exec_date: The date of execution of the task.
            user: The user to create the notification for.
        """
        pass

    @staticmethod
    @abstractmethod
    def notify(user: "User", obj: object, verb: "NotificationVerb"):
        """
        Notify the user about the entity.
        """
        pass

    @staticmethod
    def get_notification_setting(user: "User"):
        """
        Get the notification setting of the user.
        """
        from notification.models import NotificationSetting

        try:
            setting = user.notification_setting
        except Exception:
            setting = NotificationSetting(user=user)
            setting.save()
        return setting

    def get_absolute_url(self) -> Optional[str]:
        """
        Returns the absolute url of the entity.
        """
        return None
