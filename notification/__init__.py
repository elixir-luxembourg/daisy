from datetime import date


class NotifyMixin:
    @staticmethod
    def get_notification_recipients():
        """
        Should Query the users based on their notification settings
        and the entity.

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(
            f"Subclasses of {NotifyMixin.__name__} must implement {NotifyMixin.get_notification_recipients.__name__}"
        )

    @classmethod
    def make_notifications(cls, exec_date: date):
        """
        Creates a notifications for the reciepients based on
        the business logic of the entity.

        Params:
            exec_date: The date of execution

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(
            f"Subclasses of {NotifyMixin.__name__} must implement {cls.make_notification.__name__}"
        )

    @staticmethod
    def notify(obj: object, verb):
        """
        Notify the user about the entity.
        """
        raise NotImplementedError(
            f"Subclasses of {NotifyMixin.__name__} must implement {NotifyMixin.notify.__name__}"
        )

    def get_absolute_url(self):
        """
        Returns the absolute url of the entity.
        """
        return None
