from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from core.models import User
from core.reporting import generate_reports_for

class UserSelection(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(should_receive_email_reports=False), help_text='Select the user.')


@staff_member_required
def email_reports(request):
    if request.method == 'GET':
        status = getattr(settings, 'EMAIL_REPORTS_ENABLED', False)
        users = User.objects.filter(
            email__contains='@', 
            should_receive_email_reports=True
        )
        form = UserSelection(initial={})
        context = {
            'users': users,
            'status': status,
            'form': form
        }
        return render(request, 'reporting/index.html', context)
    else:
        form = UserSelection(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            user.should_receive_email_reports = True
            user.save()
        return redirect('email_reports')

@staff_member_required
def email_reports_disable_for_user(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return render(request, 'reporting/preview.html', {"error": "The user with selected ID does not exist!"})
    user.should_receive_email_reports = False
    user.save()
    return redirect('email_reports')

@staff_member_required
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
