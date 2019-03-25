from notification.email_sender import send_the_email
from django.conf import settings

def test_send_email(celery_session_worker):
    """
    Check if at least it does not throw errors
    """
    send_the_email(settings.EMAIL_DONOTREPLY, [], 'Title of the email', 'notification/notification_report', {})