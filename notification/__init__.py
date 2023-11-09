from abc import ABC, abstractmethod
import typing
from typing import List, Optional

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
    @abstractmethod
    def make_notifications(cls, exec_date: "date"):
        """
        Creates notifications for the reciepients based on
        the business logic of the entity.

        Params:
            exec_date: The date of execution of the task.
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
