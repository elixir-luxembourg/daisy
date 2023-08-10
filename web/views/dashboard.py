from django.shortcuts import render

from core.models import Dataset, Project


def dashboard(request):
    the_user = request.user

    # Getting projects related to the user
    projects_user_owns = Project.objects.filter(local_custodians=the_user)
    projects_user_is_in = Project.objects.filter(company_personnel=the_user)

    # Take only 5 most recent
    projects_user_owns_latest = projects_user_owns.order_by("added")[:5]
    projects_user_is_in_latest = projects_user_is_in.order_by("added")[:5]

    # Join together these projects
    last_projects = projects_user_owns_latest.union(projects_user_is_in_latest)

    # Getting datasets related to the user
    last_datasets = Dataset.objects.filter(local_custodians=the_user).order_by("added")[
        :5
    ]

    # Get the notifications
    # notifications = request.user.notifications.ordered()[:5]

    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects,
        # "notifications": notifications,
    }

    return render(request, "dashboard.html", context)
