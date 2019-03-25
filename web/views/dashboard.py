from django.shortcuts import render

from core.models import Dataset, Project


def dashboard(request):

    last_datasets = Dataset.objects.filter().order_by('added')[:5]
    last_projects = Project.objects.filter().order_by('added')[:5]


    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects
    }
    return render(
        request,
        'dashboard.html', context
    )
