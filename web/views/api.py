import json
import sys

from functools import wraps
from io import StringIO
from typing import Dict, Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.contrib.auth.hashers import get_hasher

from django.contrib.auth.decorators import login_not_required

from core.importer.datasets_exporter import DatasetsExporter
from core.importer.projects_exporter import ProjectsExporter
from core.lcsb.rems import handle_rems_callback
from core.lcsb.rems import synchronizer
from core.models import (
    User,
    Cohort,
    Partner,
    DiseaseTerm,
    Endpoint,
)
from core.models.term_model import TermCategory, PhenotypeTerm, StudyTerm, GeneTerm
from core.utils import DaisyLogger
from web.views.utils import get_client_ip, get_user_or_contact_by_oidc_id


logger = DaisyLogger(__name__)


def create_error_response(
    message: str, more: Optional[Dict] = None, status: int = 500
) -> JsonResponse:
    if more is None:
        more = {}
    body = {"status": "Error", "description": message}
    return JsonResponse({**more, **body}, status=status)


def create_protect_with_api_key_decorator(global_api_key=None):
    def protect_with_api_key(view):
        """
        Checks if there is a GET or POST parameter that:
        * contains either GLOBAL_API_KEY from settings
        * matches one of User's api_key attribute
        """

        @wraps(view)
        def decorator(request, *args, **kwargs):
            submitted_keys = [request.GET.get("API_KEY"), request.POST.get("API_KEY")]
            req_key = submitted_keys[0] or submitted_keys[1]
            error_message = (
                "API_KEY missing in POST or GET parameters, or its value is invalid!"
            )
            if global_api_key is not None and global_api_key in submitted_keys:
                request.COOKIES["global"] = True
                return view(request, *args, **kwargs)
            elif req_key:
                # Check the key from GET or POST from USER api_key
                if User.objects.filter(Q(api_key=req_key)).count() > 0:
                    return view(request, *args, **kwargs)
                # Check the key from GET or POST from Endpoint hashed api_key
                hashed_key = get_hasher("default").encode(
                    req_key, salt=settings.SECRET_KEY
                )
                try:
                    endpoint = Endpoint.objects.get(api_key=hashed_key)
                except Endpoint.DoesNotExist:
                    return create_error_response(
                        "There is no permitted endpoint with your API_KEY", status=403
                    )
                request.COOKIES["endpoint_id"] = endpoint.id
                return view(request, *args, **kwargs)
            else:
                return create_error_response(error_message, status=403)

        return decorator

    return protect_with_api_key


_global_api_key = (
    getattr(settings, "GLOBAL_API_KEY") if hasattr(settings, "GLOBAL_API_KEY") else None
)
protect_with_api_key = create_protect_with_api_key_decorator(_global_api_key)

"""
Rapido API method, we should probably use django rest framework if we want to develop API further.
"""


def users(request):
    return JsonResponse(
        {
            "results": [
                {"id": user.pk, "text": str(user)}
                for user in User.objects.all()
                if not user.username == "AnonymousUser"
            ]
        }
    )


@login_not_required
@csrf_exempt
def cohorts(request):
    return JsonResponse(
        {
            "results": [
                cohort.to_dict() for cohort in Cohort.objects.filter(_is_published=True)
            ]
        }
    )


@login_not_required
@csrf_exempt
def partners(request):
    return JsonResponse(
        {
            "results": [
                partner.to_dict()
                for partner in Partner.objects.filter(_is_published=True)
            ]
        }
    )


@login_not_required
def termsearch(request, category):
    search = request.GET.get("search")
    page = request.GET.get("page")

    if category == TermCategory.disease.value:
        matching_terms = DiseaseTerm.objects.filter(label__icontains=search).order_by(
            "id"
        )
    elif category == TermCategory.phenotype.value:
        matching_terms = PhenotypeTerm.objects.filter(label__icontains=search).order_by(
            "id"
        )
    elif category == TermCategory.study.value:
        matching_terms = StudyTerm.objects.filter(label__icontains=search).order_by(
            "id"
        )
    elif category == TermCategory.gene.value:
        matching_terms = GeneTerm.objects.filter(label__icontains=search).order_by("id")
    else:
        matching_terms = []

    paginator = Paginator(matching_terms, 25)

    if int(page) > paginator.num_pages:
        return HttpResponseBadRequest("invalid page parameter")

    matching_terms_on_page = paginator.get_page(page)

    results = []
    for matching_term in matching_terms_on_page:
        results.append({"id": matching_term.id, "text": matching_term.label})

    return JsonResponse(
        {"results": results, "pagination": {"more": int(page) < paginator.num_pages}}
    )


@login_not_required
@csrf_exempt
@protect_with_api_key
def datasets(request):
    endpoint_id = request.COOKIES.get("endpoint_id")
    global_export = request.COOKIES.get("global")
    objects = get_filtered_entities(request, "Dataset")
    if "project_id" in request.GET:
        project_id = request.GET.get("project_id", "")
        objects = objects.filter(project__id=project_id)
    if "project_title" in request.GET:
        project_title = request.GET.get("project_title", "")
        objects = objects.filter(project__title__iexact=project_title)
    exporter = DatasetsExporter(
        objects=objects, endpoint_id=endpoint_id, include_unpublished=global_export
    )

    try:
        buffer = exporter.export_to_buffer(StringIO())

        return HttpResponse(buffer.getvalue())
    except Exception as e:
        return create_error_response(
            "Something went wrong during exporting the datasets", {"more": str(e)}
        )


def is_valid_field_in_model(klass_name, field_name):
    getattr(klass_name, field_name, False)


def get_filtered_entities(request, model_name):
    filters = {}
    for filter_key in request.GET:
        if not is_valid_field_in_model(model_name, filter_key):
            continue
        filters[filter_key] = request.GET.get(filter_key)

    return getattr(sys.modules["core.models"], model_name).objects.filter(**filters)


@login_not_required
@csrf_exempt
@protect_with_api_key
def contracts(request):
    objects = get_filtered_entities(request, "Contract")
    objects = objects.anotate(c=Count("project__datasets__exposures")).filter(
        project__is_published=True, c__gt=0
    )
    if "project_id" in request.GET:
        project_id = request.GET.get("project_id", "")
        objects = objects.filter(project__id=project_id)
    object_dicts = []
    for contract in objects:
        cd = contract.to_dict()
        cd["source"] = settings.SERVER_URL
        object_dicts.append(cd)
    objects_json_buffer = StringIO()
    json.dump({"items": object_dicts}, objects_json_buffer, indent=4)

    try:
        return HttpResponse(objects_json_buffer.getvalue())
    except Exception as e:
        return create_error_response(
            "Something went wrong during exporting the contracts", {"more": str(e)}
        )


@login_not_required
@csrf_exempt
@protect_with_api_key
def projects(request):
    endpoint_id = request.COOKIES.get("endpoint_id")
    global_export = request.COOKIES.get("global")
    objects = get_filtered_entities(request, "Project")
    if "project_id" in request.GET:
        project_id = request.GET.get("project_id", "")
        objects = objects.filter(id=project_id)

    exporter = ProjectsExporter(
        objects=objects, endpoint_id=endpoint_id, include_unpublished=global_export
    )

    try:
        buffer = exporter.export_to_buffer(StringIO())

        return HttpResponse(buffer.getvalue())
    except Exception as e:
        return create_error_response(
            "Something went wrong during exporting the projects", {"more": str(e)}
        )


@login_not_required
@csrf_exempt
def rems_endpoint(request):
    try:
        if not getattr(settings, "REMS_INTEGRATION_ENABLED", False):
            raise Warning(f"REMS endpoint called, but it" "s disabled.")

        ip = get_client_ip(request)
        logger.debug(f"REMS endpoint called from: {ip}...")

        allowed_ips = getattr(settings, "REMS_ALLOWED_IP_ADDRESSES", [])
        skip_check_setting = getattr(settings, "REMS_SKIP_IP_CHECK", False)
        if "*" in allowed_ips:
            skip_check_setting = True

        if len(allowed_ips) == 0 and not skip_check_setting:
            raise Warning(f"REMS - the IP whitelist is empty, import failed!")

        if ip not in allowed_ips and not skip_check_setting:
            raise Warning(f"REMS - the IP is not in the whitelist, import failed!")

        status = True if handle_rems_callback(request) else False
        logger.debug(f"REMS - was import successful?: {status}!")
        if status:
            return JsonResponse({"status": "Success"}, status=200)
        else:
            return JsonResponse({"status": "Failure"}, status=500)
    except (Warning, ImproperlyConfigured) as ex:
        message = f"REMS - something is wrong with the configuration!"
        more = str(ex)
        logger.debug(f"{message} ({more})")
        return create_error_response(message)
    except Exception as ex:
        message = f"REMS - something went wrong during the import!"
        more = str(ex)
        logger.debug(f"{message} ({more}")
        return create_error_response(message, {"more": more})


@login_not_required
@csrf_exempt
@protect_with_api_key
def force_keycloak_synchronization(request) -> JsonResponse:
    try:
        logger.debug("Forcing refreshing the account information from Keycloak...")
        synchronizer.synchronize_all()
        logger.debug("...successfully refreshed the information from Keycloak!")
        return JsonResponse(
            f"OK ({synchronizer.__class__.__name__})", status=200, safe=False
        )
    except Exception as ex:
        return JsonResponse(
            f"Something went wrong (using: {synchronizer.__class__.__name__}): {ex}",
            status=500,
            safe=False,
        )


@login_not_required
@csrf_exempt
@protect_with_api_key
def permissions(request, user_oidc_id: str) -> JsonResponse:
    system_daisy_user, created = User.objects.get_or_create(
        username="system::daisy",
    )
    if created:
        system_daisy_user.email = "lcsb.sysadmins+daisy@uni.lu"
        system_daisy_user.save()

    logger.debug("Permission API endpoint called...")
    user_found, contact_found, user, contact = get_user_or_contact_by_oidc_id(
        user_oidc_id
    )
    logger.debug(
        "...found User: " + str(user_found) + ", found Contact: " + str(contact_found)
    )

    if not user_found and not contact_found:
        message = "No contact nor user found!"
        logger.debug(message)
        return create_error_response(message, status=404)

    try:
        if user:
            permissions = user.get_access_permissions()
            return JsonResponse(permissions, status=200, safe=False)
        elif contact:
            permissions = contact.get_access_permissions()
            return JsonResponse(permissions, status=200, safe=False)
    except Exception as e:
        message = "Something went wrong during exporting the permissions"
        more = str(e)
        logger.debug(f"{message} ({more}")
        return create_error_response(message, {"more": more}, status=404)
