"""
Some routines concerning e-mail generation and sending
"""

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


SUBJECT_PREFIX = '[DAISY]'

def send_email_from_template(sender_email, recipients, subject, template, context):
    """
    Generates and sends an email message from html/txt template
    """
    
    # Update context with server's full url if it's not present already
    if 'server_url' not in context:
        context['server_url'] = '%s://%s' % (settings.SERVER_SCHEME, settings.SERVER_URL)
    if 'profile_url' not in context:
        context['profile_url'] = reverse('profile')

    # Prepare the email
    text_message = render_to_string('%s.txt' % template, context)
    html_message = render_to_string('%s.html' % template, context)

    return send_the_email(sender_email, recipients, subject, text_message, html_message)

def send_the_email(sender_email, recipients, subject, text_message, html_message=None):
    """
    Send an email to the recipents using given txt and html messages
    """
    # Recipients can be a list or single email
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]
    
    _send_the_email(sender_email, recipients, subject, text_message, html_message, False)


def _send_the_email(sender_email, recipients, subject, text_message, html_message, fail_silently):
    msg = EmailMultiAlternatives(
        subject,
        text_message,
        sender_email,
        recipients
    )
    if html_message is not None:
        msg.attach_alternative(html_message, 'text/html')
    msg.send(fail_silently=fail_silently)