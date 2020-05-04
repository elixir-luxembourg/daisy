from django.shortcuts import render


def custom_error(request, exception, reason, status):
    context = {
        'reason': reason,
        'exception': exception
    }
    return render(request, 'error.html', context, status=status)

def custom_csrf(request, exception):
    return custom_error(request, exception, 'csrf', 400)

def custom_400(request, exception):
    return custom_error(request, exception, '400', 400)

def custom_403(request, exception):
    return custom_error(request, exception, '403', 403)

def custom_404(request, exception):
    return custom_error(request, exception, '404', 404)

def custom_500(request, exception):
    return custom_error(request, exception, '500', 500)
