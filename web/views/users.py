from django.contrib import messages
from django.contrib.messages import add_message
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.forms.user import PickUserForm
from core.models import Project
from core.models import User
from core.permissions import permission_required


@permission_required('EDIT', (Project, 'pk', 'pk'))
def add_personnel_to_project(request, pk):
    if request.method == 'POST':
        form = PickUserForm(request.POST)
        if form.is_valid():
            project = get_object_or_404(Project, pk=pk)
            user_id = form.cleaned_data['personnel']
            personnel = get_object_or_404(User, pk=user_id)
            project.company_personnel.add(personnel)
            project.save()
            add_message(request, messages.SUCCESS, "Personnel added")
        else:
            error_messages = []
            for field, error in form.errors.items():
                error_message = "{}: {}".format(field, error[0])
                error_messages.append(error_message)
            add_message(request, messages.ERROR, "\n".join(error_messages))
        return redirect(to='project', pk=pk)

    else:
        form = PickUserForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


@require_http_methods(["DELETE"])
@permission_required('EDIT', (Project, 'pk', 'pk'))
def remove_personnel_from_project(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    project.company_personnel.remove(user_id)
    project.save()
    return HttpResponse("Personnel removed")
