from django.conf import settings

from notification.email_sender import send_email_from_template


def test_send_email(celery_session_worker):
    """
    Check if at least it does not throw errors
    """
    send_email_from_template(settings.EMAIL_DONOTREPLY, [], 'Title of the email', 'notification/notification_report', {})