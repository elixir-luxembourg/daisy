"""
Template for email
"""
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

SUBJECT_PREFIX = '[DAISY]'


def send_the_email(sender_email, recipients, subject, template, context):
    """
    Send an email to the recipents using the templates,
    """
    # recipients can be a list or single email
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]
    # update context with server full url if it's not present already
    if 'server_url' not in context:
        context['server_url'] = '%s://%s' % (settings.SERVER_SCHEME, settings.SERVER_URL)
    if 'profile_url' not in context:
        context['profile_url'] = reverse('profile')

    # prepare email
    subject = "{p} {s}".format(p=SUBJECT_PREFIX, s=subject)
    text_message = render_to_string('%s.txt' % template, context)
    html_message = render_to_string('%s.html' % template, context)
    msg = EmailMultiAlternatives(
        subject,
        text_message,
        sender_email,
        recipients
    )
    msg.attach_alternative(html_message, 'text/html')
    msg.send(fail_silently=False)