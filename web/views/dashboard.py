from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from core.constants import Groups
from core.models import Access, Dataset, Project
from core.models.access import StatusChoices
from core.models.data_declaration import DataDeclaration
from notification.models import Notification

ATTENTION_ITEMS_CAP = 8


def dashboard(request, template_name="dashboard.html"):
    the_user = request.user
    today = timezone.localdate()
    soon = today + timedelta(days=30)

    projects_user_owns = Project.objects.filter(local_custodians=the_user)
    projects_user_is_in = Project.objects.filter(company_personnel=the_user)

    projects_user_owns_latest = projects_user_owns.order_by("-added")[:5]
    projects_user_is_in_latest = projects_user_is_in.order_by("-added")[:5]

    last_projects = projects_user_owns_latest.union(projects_user_is_in_latest)
    last_datasets = Dataset.objects.filter(local_custodians=the_user).order_by(
        "-added"
    )[:5]

    is_steward = the_user.is_superuser or the_user.is_part_of(Groups.DATA_STEWARD.value)
    can_manage_accesses = is_steward or the_user.is_part_of(Groups.VIP.value)

    accesses_expiring = None
    accesses_expiring_count = 0
    retention_reached = None
    retention_reached_count = 0
    if can_manage_accesses:
        custodied = Q(dataset__local_custodians=the_user) | Q(
            dataset__project__local_custodians=the_user
        )
        accesses = Access.objects.filter(
            status=StatusChoices.active,
            grant_expires_on__isnull=False,
            grant_expires_on__lte=soon,
        )
        declarations = DataDeclaration.objects.filter(
            end_of_storage_duration__lte=today
        )
        if not is_steward:
            accesses = accesses.filter(custodied)
            declarations = declarations.filter(custodied)
        accesses = (
            accesses.select_related("dataset", "user", "contact")
            .distinct()
            .order_by("grant_expires_on")
        )
        declarations = (
            declarations.select_related("dataset")
            .distinct()
            .order_by("end_of_storage_duration")
        )
        accesses_expiring_count = accesses.count()
        retention_reached_count = declarations.count()
        accesses_expiring = accesses[:ATTENTION_ITEMS_CAP]
        retention_reached = declarations[:ATTENTION_ITEMS_CAP]

    deadlines = None
    deadlines_count = 0
    notifications_enabled = not getattr(settings, "NOTIFICATIONS_DISABLED", True)
    if notifications_enabled:
        deadline_qs = Notification.objects.filter(
            recipient=the_user,
            dismissed=False,
            dispatch_in_app=True,
            on__date__gte=today,
        ).order_by("on")
        deadlines_count = deadline_qs.count()
        deadlines = deadline_qs[:ATTENTION_ITEMS_CAP]

    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects,
        "today": today,
        "show_attention": can_manage_accesses or notifications_enabled,
        "can_manage_accesses": can_manage_accesses,
        "accesses_expiring": accesses_expiring,
        "accesses_expiring_count": accesses_expiring_count,
        "accesses_expiring_more": max(0, accesses_expiring_count - ATTENTION_ITEMS_CAP),
        "retention_reached": retention_reached,
        "retention_reached_count": retention_reached_count,
        "retention_reached_more": max(0, retention_reached_count - ATTENTION_ITEMS_CAP),
        "deadlines": deadlines,
        "deadlines_count": deadlines_count,
    }
    return render(request, template_name, context)
