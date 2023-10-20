class NotifyMixin:
    def get_notification_recipients(self):
        """
        Should Query the users based on their notification settings 
        and the entity.

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(f"Subclasses of {NotifyMixin.__name__} must implement {self.get_notification_recipients.__name__}")
    
    def make_notification(self):
        """
        Creates a notifications for the reciepients based on 
        the business logic of the entity.

        Raises:
            NotImplementedError: It should be implemented by the subclass
        """
        raise NotImplementedError(f"Subclasses of {NotifyMixin.__name__} must implement {self.make_notification.__name__}")
    
    def get_absolute_url(self):
        """
        Returns the absolute url of the entity.
        """
        return None