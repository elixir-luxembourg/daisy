import json
import os

from functools import wraps
from io import StringIO
from typing import Dict, Optional

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from ontobio import obograph_util, Ontology

from stronghold.decorators import public

from core.importer.datasets_exporter import DatasetsExporter
from core.importer.projects_exporter import ProjectsExporter
from core.models import User, Cohort, Dataset, Partner, Project, DiseaseTerm
from core.models.term_model import TermCategory, PhenotypeTerm, StudyTerm, GeneTerm
from core.utils import DaisyLogger
from elixir_daisy import settings
from web.lcsb import handle_rems_callback
from web.views.utils import get_client_ip




logger = DaisyLogger(__name__)


def create_error_response(message: str, more: Optional[Dict]={}, status: int=500) -> JsonResponse:
    body = {
        'status': 'Error',
        'description': message
    }
    return JsonResponse({**more, **body}, status=status)

def protect_with_api_key(view):
    """
    Checks if there is a GET or POST parameter that:
     * contains either GLOABAL_API_KEY from settings
     * matches one of User's api_key attribute
    """
    @wraps(view)
    def decorator(request, *args, **kwargs):
        submitted_keys = [request.GET.get('API_KEY', '-'), request.POST.get('API_KEY', '-')]
        error_message = 'API_KEY missing in POST or GET parameters, or its value is invalid!'
        if 'API_KEY' not in request.GET and 'API_KEY' not in request.POST:
            return create_error_response(error_message, status=403)
        elif hasattr(settings, 'GLOBAL_API_KEY') and getattr(settings, 'GLOBAL_API_KEY') in submitted_keys:
            return view(request, *args, **kwargs)
        # Check the key from GET
        elif submitted_keys[0] not in ['-', ''] and User.objects.filter(api_key=submitted_keys[0]).count() > 0:
            return view(request, *args, **kwargs)
        # Check the key from POST
        elif submitted_keys[1] not in ['-', ''] and User.objects.filter(api_key=submitted_keys[1]).count() > 0:
            return view(request, *args, **kwargs)
        return create_error_response(error_message, status=403)
    return decorator

"""
Rapido API method, we should probably use django rest framework if we want to develop API further.
"""
def users(request):
    return JsonResponse({
        "results": [{"id": user.pk, "text": str(user)}
                    for user in User.objects.all() if not user.username == 'AnonymousUser']
    })

@public
@csrf_exempt
def cohorts(request):
    return JsonResponse({
        "results": [cohort.to_dict() for cohort in Cohort.objects.filter(is_published=True)]
    })

@public
@csrf_exempt
def partners(request):
    return JsonResponse({
        "results": [partner.to_dict() for partner in Partner.objects.filter(is_published=True)]
    })

@public
def termsearch(request, category):
    search = request.GET.get('search')
    page = request.GET.get('page')

    if category == TermCategory.disease.value:
        matching_terms = DiseaseTerm.objects.filter(label__icontains=search).order_by('id')
    elif category == TermCategory.phenotype.value:
        matching_terms = PhenotypeTerm.objects.filter(label__icontains=search).order_by('id')
    elif category == TermCategory.study.value:
        matching_terms = StudyTerm.objects.filter(label__icontains=search).order_by('id')
    elif category == TermCategory.gene.value:
        matching_terms = GeneTerm.objects.filter(label__icontains=search).order_by('id')
    else:
        matching_terms = []

    paginator = Paginator(matching_terms, 25)

    if int(page) > paginator.num_pages:
        return HttpResponseBadRequest("invalid page parameter")

    matching_terms_on_page = paginator.get_page(page)

    results = []
    for matching_term in matching_terms_on_page:
        results.append({
            "id": matching_term.id,
            "text": matching_term.label
        })

    return JsonResponse({
        "results": results,
        "pagination": {
            "more": int(page) < paginator.num_pages
        }
    })

@public
@csrf_exempt
@protect_with_api_key
def datasets(request):
    if 'project_title' in request.GET:
        project_title = request.GET.get('project_title', '')
        datasets = Dataset.objects.filter(project__title__iexact=project_title, is_published=True)
        exporter = DatasetsExporter(datasets)
    else:
        datasets = Dataset.objects.filter(is_published=True)
        exporter = DatasetsExporter(datasets)

    try:
        buffer = exporter.export_to_buffer(StringIO())

        return HttpResponse(buffer.getvalue())
    except Exception as e:
        return create_error_response(
            'Something went wrong during exporting the datasets',
            {'more': str(e)}
        )

@public
@csrf_exempt
@protect_with_api_key
def projects(request):
    if 'title' in request.GET:
        title = request.GET.get('title', '')
        projects = Project.objects.filter(title__iexact=title, is_published=True)
        exporter = ProjectsExporter(projects)
    else:
        projects = Project.objects.filter(is_published=True)
        exporter = ProjectsExporter(projects)

    try:
        buffer = exporter.export_to_buffer(StringIO())

        return HttpResponse(buffer.getvalue())
    except Exception as e:
        return create_error_response(
            'Something went wrong during exporting the projects',
            {'more': str(e)}
        )

@public
@csrf_exempt
def rems_endpoint(request):
    if not getattr(settings, 'REMS_INTEGRATION_ENABLED', False):
        message = f'REMS endpoint called, but it''s disabled.'
        logger.debug(message)
        return create_error_response(message)
        
    ip = get_client_ip(request)
    logger.debug(f'REMS endpoint called from: {ip}...')

    allowed_ips = getattr(settings, 'REMS_ALLOWED_IP_ADDRESSES', [])
    skip_check_setting = getattr(settings, 'REMS_SKIP_IP_CHECK', False)
    if '*' in allowed_ips:
        skip_check_setting = True

    if len(allowed_ips) == 0 and not skip_check_setting:
        message = f'REMS - the list of allowed IPs is empty, import failed!'
        logger.debug(message)
        return create_error_response(message)

    if ip not in allowed_ips and not skip_check_setting:
        message = f'REMS - the IP is not in the list of allowed IPs, import failed!'
        logger.debug(message)
        return create_error_response(message)
    
    try:
        status = "Success" if handle_rems_callback(request) else "Failure"
        logger.debug(f'REMS - import status: {status}!')
        return JsonResponse({'status': f'{status}'}, status=200)
    except Exception as ex:
        message = f'REMS - something went wrong during the import!'
        logger.debug(message)
        return create_error_response(message, {'more': str(ex)})


@public
@csrf_exempt
@protect_with_api_key
def permissions(request, user_oidc_id: str) -> JsonResponse:
    try:
        user = User.objects.get(oidc_id=user_oidc_id)
        permissions = user.get_access_permissions()
        return JsonResponse(permissions, status=200, safe=False)
    except Exception as e:
        return create_error_response(
            'Something went wrong during exporting the permissions',
            {'more': str(e)}
        )
