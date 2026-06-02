from datetime import timedelta

from django.conf import settings
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.utils import timezone

from auditlog.models import LogEntry
from core.constants import Groups
from core.models import Access, Cohort, Contract, Dataset, Project
from core.models.access import StatusChoices
from core.models.dac import DAC
from core.models.data_declaration import ConsentStatus, DataDeclaration, ShareCategory
from core.models.partner import Partner
from notification.models import Notification


def dashboard(request):
    the_user = request.user

    projects_user_owns = Project.objects.filter(local_custodians=the_user)
    projects_user_is_in = Project.objects.filter(company_personnel=the_user)

    projects_user_owns_latest = projects_user_owns.order_by("added")[:5]
    projects_user_is_in_latest = projects_user_is_in.order_by("added")[:5]

    last_projects = projects_user_owns_latest.union(projects_user_is_in_latest)
    last_datasets = Dataset.objects.filter(local_custodians=the_user).order_by("added")[
        :5
    ]

    context = {
        "last_datasets": last_datasets,
        "last_projects": last_projects,
    }
    return render(request, "dashboard.html", context)


def landing(request):
    user = request.user
    today = timezone.localdate()
    soon = today + timedelta(days=90)
    published = Q(exposures__is_deprecated=False)

    if user.is_superuser or user.is_part_of(Groups.DATA_STEWARD.value):
        role = "steward"
    elif user.is_part_of(Groups.AUDITOR.value):
        role = "auditor"
    elif user.is_part_of(Groups.LEGAL.value):
        role = "legal"
    elif user.is_part_of(Groups.VIP.value):
        role = "vip"
    else:
        role = "researcher"

    custodied_projects = (
        Project.objects.filter(Q(local_custodians=user) | Q(company_personnel=user))
        .distinct()
        .order_by("-updated")
    )
    custodied_datasets = (
        Dataset.objects.filter(
            Q(local_custodians=user) | Q(project__local_custodians=user)
        )
        .distinct()
        .order_by("-updated")
    )
    custodied_contracts = (
        Contract.objects.filter(
            Q(local_custodians=user) | Q(project__local_custodians=user)
        )
        .select_related("project")
        .prefetch_related("partners_roles__partner")
        .distinct()
        .order_by("-updated")
    )
    active_custodied_accesses = (
        Access.objects.filter(
            Q(dataset__local_custodians=user)
            | Q(dataset__project__local_custodians=user),
            status=StatusChoices.active,
        )
        .select_related("dataset", "user", "contact")
        .distinct()
        .order_by("grant_expires_on")
    )

    if role in {"researcher", "vip"}:
        datasets = Dataset.objects.filter(
            Q(local_custodians=user) | Q(project__local_custodians=user)
        ).distinct()
        declarations = (
            DataDeclaration.objects.filter(
                Q(dataset__local_custodians=user)
                | Q(dataset__project__local_custodians=user)
            )
            .select_related("dataset")
            .distinct()
        )
        contracts = (
            Contract.objects.filter(
                Q(local_custodians=user) | Q(project__local_custodians=user)
            )
            .select_related("project")
            .prefetch_related("partners_roles__partner")
            .distinct()
        )
        projects = Project.objects.filter(
            Q(local_custodians=user) | Q(company_personnel=user)
        ).distinct()
        accesses = (
            Access.objects.filter(
                Q(dataset__local_custodians=user)
                | Q(dataset__project__local_custodians=user)
            )
            .select_related("dataset", "user", "contact")
            .distinct()
        )
    else:
        datasets = Dataset.objects.all()
        declarations = DataDeclaration.objects.select_related("dataset")
        contracts = Contract.objects.select_related("project").prefetch_related(
            "partners_roles__partner"
        )
        projects = Project.objects.all()
        accesses = Access.objects.select_related("dataset", "user", "contact")

    deadlines = []
    if not getattr(settings, "NOTIFICATIONS_DISABLED", True):
        deadlines = (
            Notification.objects.filter(
                recipient=user,
                dismissed=False,
                dispatch_in_app=True,
                on__date__gte=today,
            )
            .select_related("content_type")
            .prefetch_related("content_object")
            .order_by("on")
        )

    context = {
        "page_size": 5,
        "dashboard_role": role,
        "deadlines": deadlines,
        "projects": custodied_projects,
        "datasets": custodied_datasets,
        "contracts": custodied_contracts,
        "accesses": active_custodied_accesses,
        "retention_reached": declarations.filter(end_of_storage_duration__lte=today)
        .annotate(signal_date=F("end_of_storage_duration"))
        .order_by("end_of_storage_duration"),
        "retention_approaching": declarations.filter(
            end_of_storage_duration__gt=today,
            end_of_storage_duration__lte=soon,
        )
        .annotate(signal_date=F("end_of_storage_duration"))
        .order_by("end_of_storage_duration"),
        "datasets_embargo_unpublished": datasets.filter(
            data_declarations__embargo_date__lte=today
        )
        .exclude(published)
        .distinct()
        .order_by("-updated"),
        "projects_ended_live": projects.filter(end_date__lt=today)
        .filter(
            Q(datasets__accesses__status=StatusChoices.active)
            | Q(datasets__exposures__is_deprecated=False)
        )
        .annotate(signal_date=F("end_date"))
        .distinct()
        .order_by("end_date"),
        "datasets_no_legal_basis": datasets.filter(legal_basis_definitions__isnull=True)
        .distinct()
        .order_by("-updated"),
        "datasets_no_declaration": datasets.filter(
            data_declarations__isnull=True
        ).order_by("-updated"),
        "datasets_no_storage": datasets.filter(data_locations__isnull=True)
        .distinct()
        .order_by("-updated"),
        "datasets_no_custodian": datasets.filter(
            local_custodians__isnull=True
        ).order_by("-updated"),
        "datasets_orphan": datasets.filter(project__isnull=True).order_by("-updated"),
        "consent_unknown": declarations.filter(
            consent_status=ConsentStatus.unknown
        ).order_by("-updated"),
        "special_subjects_undocumented": declarations.filter(has_special_subjects=True)
        .filter(
            Q(special_subjects_description__isnull=True)
            | Q(special_subjects_description="")
        )
        .order_by("-updated"),
        "data_received_no_contract": declarations.filter(
            partner__isnull=False,
            contract__isnull=True,
        ).order_by("-updated"),
        "contracts_unsigned": contracts.filter(partners_roles__isnull=True)
        .distinct()
        .order_by("-updated"),
        "contracts_no_documents": contracts.annotate(
            doc_count=Count("legal_documents", distinct=True)
        )
        .filter(doc_count=0)
        .order_by("-updated"),
        "contracts_no_gdpr_role": contracts.filter(
            partners_roles__isnull=False,
            partners_roles__roles__isnull=True,
        )
        .distinct()
        .order_by("-updated"),
        "contracts_standalone": contracts.filter(project__isnull=True).order_by(
            "-updated"
        ),
        "datasets_transfer_no_contract": datasets.filter(
            shares__isnull=False,
            shares__contract__isnull=True,
        )
        .distinct()
        .order_by("-updated"),
        "datasets_controlled_no_dac": datasets.filter(
            data_declarations__share_category=ShareCategory.controlled_access,
            dac__isnull=True,
        )
        .distinct()
        .order_by("-updated"),
        "projects_no_ethics": projects.filter(has_cner=False, has_erp=False).order_by(
            "-updated"
        ),
        "datasets_ready_to_publish": datasets.filter(
            legal_basis_definitions__isnull=False,
            data_declarations__embargo_date__lte=today,
        )
        .exclude(published)
        .distinct()
        .order_by("-updated"),
        "access_precreated": accesses.filter(status=StatusChoices.precreated).order_by(
            "-added"
        ),
        "access_suspended": accesses.filter(status=StatusChoices.suspended).order_by(
            "-added"
        ),
        "access_open_ended": accesses.filter(
            status=StatusChoices.active,
            grant_expires_on__isnull=True,
        ).order_by("-added"),
        "expiring_accesses": accesses.filter(
            status=StatusChoices.active,
            grant_expires_on__isnull=False,
            grant_expires_on__gte=today,
            grant_expires_on__lte=today + timedelta(days=30),
        ).order_by("grant_expires_on"),
        "overdue_accesses": accesses.filter(
            status=StatusChoices.active,
            grant_expires_on__isnull=False,
            grant_expires_on__lt=today,
        ).order_by("grant_expires_on"),
    }

    if role == "steward":
        context.update(
            {
                "unpublished_partners": Partner.objects.filter(
                    _is_published=False
                ).order_by("-id"),
                "unpublished_cohorts": Cohort.objects.filter(
                    _is_published=False
                ).order_by("-id"),
                "dacs_no_members": DAC.objects.filter(members__isnull=True).order_by(
                    "-updated"
                ),
                "rems_access": accesses.filter(
                    was_generated_automatically=True
                ).order_by("-added"),
            }
        )
    elif role == "auditor":
        context.update(
            {
                "recent_activity": LogEntry.objects.filter(
                    timestamp__gte=timezone.now() - timedelta(days=30)
                )
                .select_related("actor", "content_type")
                .order_by("-timestamp"),
                "recent_datasets": Dataset.objects.order_by("-updated"),
                "recent_projects": Project.objects.order_by("-updated"),
                "recent_contracts": contracts.order_by("-updated"),
                "dacs_no_members": DAC.objects.filter(members__isnull=True).order_by(
                    "-updated"
                ),
            }
        )
    elif role == "legal":
        context.update(
            {
                "all_contracts": contracts.order_by("-updated"),
                "dacs_no_members": DAC.objects.filter(members__isnull=True).order_by(
                    "-updated"
                ),
            }
        )

    return render(request, "landing.html", context)
