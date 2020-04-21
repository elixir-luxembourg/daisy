from django.shortcuts import render

from core.models import Dataset, Project


def dashboard(request):
    the_user = request.user

    # Getting projects related to the user
    projects_user_owns = Project.objects.filter(local_custodians=the_user)
    # projects_user_is_in = Project.objects.filter()
    # last_projects = Project.objects.filter().order_by('added')[:5]
    last_projects = projects_user_owns.order_by('added')[:5]

    # Getting datasets related to the user
    last_datasets = Dataset.objects.filter().order_by('added')[:5]

    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects
    }
    return render(
        request,
        'dashboard.html', context
    )
