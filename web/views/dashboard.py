from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from core.models import Access, Contract, Dataset, Project
from core.models.access import StatusChoices
from notification.models import Notification


def dashboard(request):
    the_user = request.user

    projects = (
        Project.objects.filter(local_custodians=the_user)
        | Project.objects.filter(company_personnel=the_user)
    ).distinct().order_by("-updated")
    datasets = Dataset.objects.filter(local_custodians=the_user).order_by("-updated")
    contracts = (
        Contract.objects.filter(local_custodians=the_user)
        .select_related("project")
        .order_by("-updated")
    )

    deadlines = []
    if not getattr(settings, "NOTIFICATIONS_DISABLED", True):
        deadlines = (
            Notification.objects.filter(
                recipient=the_user,
                dismissed=False,
                on__gte=timezone.now(),
            )
            .select_related("content_type")
            .prefetch_related("content_object")
            .order_by("on")
        )

    accesses = (
        Access.objects.filter(
            dataset__local_custodians=the_user,
            status=StatusChoices.active,
        )
        .select_related("dataset", "user", "contact")
        .order_by("grant_expires_on")
    )

    context = {
        "datasets": datasets,
        "projects": projects,
        "contracts": contracts,
        "deadlines": deadlines,
        "accesses": accesses,
        "page_size": 3,
    }

    return render(request, "dashboard.html", context)
