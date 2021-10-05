from django.shortcuts import render

from core.models import User
from core.reporting import generate_reports_for


def email_reports(request):
    users = User.objects.filter(
        email__contains='@', 
        should_receive_email_reports=True
    )
    context = {
        'users': users
    }
    return render(request, 'reporting/index.html', context)


def email_reports_preview(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return render(request, 'reporting/preview.html', {"error": "The user with selected ID does not exist!"})

    html_contents, txt_contents = generate_reports_for(user)
    context = {
        'user': user,
        'html_contents': html_contents,
        'txt_contents': txt_contents
    }
    return render(request, 'reporting/preview.html', context)
