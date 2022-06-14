from typing import List, Tuple

from django.contrib.auth.models import AbstractBaseUser
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import render

from core.models import Dataset, Project


def find_last_datasets_and_projects(the_user: AbstractBaseUser) -> Tuple[List[Dataset], List[Project]]:
    # Getting projects related to the user
    projects_user_owns = Project.objects.filter(local_custodians=the_user)
    projects_user_is_in = Project.objects.filter(company_personnel=the_user)
    
    # Take only 5 most recent
    projects_user_owns_latest = projects_user_owns.order_by('added')[:5]
    projects_user_is_in_latest = projects_user_is_in.order_by('added')[:5]

    # Join together these projects
    last_projects = projects_user_owns_latest.union(projects_user_is_in_latest)

    # Getting datasets related to the user
    last_datasets = Dataset.objects.filter(local_custodians=the_user).order_by('added')[:5]

    # Return lists instead of QuerySets
    return list(last_datasets), list(last_projects)


def dashboard(request: HttpRequest) -> HttpResponse:
    the_user = request.user

    if the_user.is_anonymous():
        last_datasets = last_projects = []
    else:
        last_datasets, last_projects = find_last_datasets_and_projects(the_user)
    
    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects,
    }

    # Get the notifications
    # notifications = request.user.notifications.ordered()[:5]

    return render(
        request,
        'dashboard.html', context
    )
