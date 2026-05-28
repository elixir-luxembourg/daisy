from datetime import timedelta

from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from core.constants import Groups
from core.models import Access, Cohort, Contract, Dataset, Project
from core.models.access import StatusChoices
from core.models.partner import Partner
from notification.models import Notification


ROLE_PARTIALS = {
    "steward": "_includes/dashboard/role_steward.html",
    "auditor": "_includes/dashboard/role_auditor.html",
    "legal": "_includes/dashboard/role_legal.html",
    "vip": "_includes/dashboard/role_vip.html",
    "researcher": "_includes/dashboard/role_researcher.html",
}


def resolve_dashboard_role(user):
    """Highest-privilege group wins; a user in several groups gets one dashboard."""
    if user.is_superuser or user.is_part_of(Groups.DATA_STEWARD.value):
        return "steward"
    if user.is_part_of(Groups.AUDITOR.value):
        return "auditor"
    if user.is_part_of(Groups.LEGAL.value):
        return "legal"
    if user.is_part_of(Groups.VIP.value):
        return "vip"
    return "researcher"


def _deadlines(user):
    if getattr(settings, "NOTIFICATIONS_DISABLED", True):
        return []
    return (
        Notification.objects.filter(
            recipient=user, dismissed=False, on__gte=timezone.now()
        )
        .select_related("content_type")
        .prefetch_related("content_object")
        .order_by("on")
    )


def _custodied(user):
    projects = (
        (
            Project.objects.filter(local_custodians=user)
            | Project.objects.filter(company_personnel=user)
        )
        .distinct()
        .order_by("-updated")
    )
    datasets = Dataset.objects.filter(local_custodians=user).order_by("-updated")
    contracts = (
        Contract.objects.filter(local_custodians=user)
        .select_related("project")
        .order_by("-updated")
    )
    accesses = (
        Access.objects.filter(
            dataset__local_custodians=user, status=StatusChoices.active
        )
        .select_related("dataset", "user", "contact")
        .order_by("grant_expires_on")
    )
    return {
        "projects": projects,
        "datasets": datasets,
        "contracts": contracts,
        "accesses": accesses,
    }


def _expiring_accesses(days=30):
    today = timezone.now().date()
    return (
        Access.objects.filter(
            status=StatusChoices.active,
            grant_expires_on__isnull=False,
            grant_expires_on__gte=today,
            grant_expires_on__lte=today + timedelta(days=days),
        )
        .select_related("dataset", "user", "contact")
        .order_by("grant_expires_on")
    )


def _researcher_ctx(user):
    ctx = _custodied(user)
    ctx.pop("contracts")
    return ctx


def _vip_ctx(user):
    return _custodied(user)


def _legal_ctx(user):
    return {
        "contracts": Contract.objects.filter(local_custodians=user)
        .select_related("project")
        .order_by("-updated"),
        "all_contracts": Contract.objects.select_related("project").order_by(
            "-updated"
        )[:10],
    }


def _auditor_ctx(user):
    return {
        "recent_datasets": Dataset.objects.order_by("-updated")[:10],
        "recent_projects": Project.objects.order_by("-updated")[:10],
        "recent_contracts": Contract.objects.select_related("project").order_by(
            "-updated"
        )[:10],
        "expiring_accesses": _expiring_accesses(),
    }


def _steward_ctx(user):
    ctx = _custodied(user)
    ctx.update(
        {
            "unpublished_partners": Partner.objects.filter(_is_published=False).order_by(
                "-id"
            )[:10],
            "unpublished_cohorts": Cohort.objects.filter(_is_published=False).order_by(
                "-id"
            )[:10],
            "expiring_accesses": _expiring_accesses(),
        }
    )
    return ctx


ROLE_CONTEXT = {
    "steward": _steward_ctx,
    "auditor": _auditor_ctx,
    "legal": _legal_ctx,
    "vip": _vip_ctx,
    "researcher": _researcher_ctx,
}


def dashboard(request):
    user = request.user
    role = resolve_dashboard_role(user)
    context = {
        "page_size": 3,
        "dashboard_role": role,
        "dashboard_partial": ROLE_PARTIALS[role],
        "deadlines": _deadlines(user),
    }
    context.update(ROLE_CONTEXT[role](user))
    return render(request, "dashboard.html", context)
