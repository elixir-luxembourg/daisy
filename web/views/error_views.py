from django.conf import settings
from django.shortcuts import render


ERROR_VIEW = 'error.html'

def make_context(reason: str, exception) -> dict:
    helpdesk_email = getattr(settings, 'HELPDESK_EMAIL')
    return {
        'reason': reason,
        'exception': exception,
        'helpdesk_email': helpdesk_email
    }

def custom_error(request, exception, reason, status):
    context = make_context(reason, exception)
    return render(request, ERROR_VIEW, context, status=status)

def custom_csrf(request, reason):
    context = make_context('csrf', reason)
    return render(request, ERROR_VIEW, context, status=400)

def custom_400(request, exception):
    return custom_error(request, exception, '400', 400)

def custom_403(request, exception):
    return custom_error(request, exception, '403', 403)

def custom_404(request, exception):
    return custom_error(request, exception, '404', 404)

def custom_500(request, exception):
    return custom_error(request, 'Server Error', '500', 500)
