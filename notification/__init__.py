from django.db.models.query import QuerySet


class NotifyMixin:
    @classmethod
    def get_notification_recipients(cls):
        """
        Should Query the users based on their notification settings
        and the entity.

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(
            f"Subclasses of {NotifyMixin.__name__} must implement {cls.get_notification_recipients.__name__}"
        )

    @classmethod
    def make_notification(cls, recipients: QuerySet):
        """
        Creates a notifications for the reciepients based on
        the business logic of the entity.

        Params:
            recipients: The users to notify

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(
            f"Subclasses of {NotifyMixin.__name__} must implement {cls.make_notification.__name__}"
        )

    def get_absolute_url(self):
        """
        Returns the absolute url of the entity.
        """
        return None
