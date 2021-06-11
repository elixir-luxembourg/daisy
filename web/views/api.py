import json
import os

from io import StringIO

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
from web.lcsb import handle_rems_callback
from web.views.utils import get_client_ip

from elixir_daisy import settings


logger = DaisyLogger(__name__)


"""
Rapido API method, we should probably use django rest framework if we want to develop API further.
"""
def users(request):
    #     "results": [
    #     {
    #       "id": 1,
    #       "text": "Option 1"
    #     },
    #     {
    #       "id": 2,
    #       "text": "Option 2"
    #     }
    #   ],
    #   "pagination": {
    #     "more": true
    #   }
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
def datasets(request):
    if 'API_KEY' not in request.GET:
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)
    elif request.GET.get('API_KEY') != getattr(settings, 'GLOBAL_API_KEY'):
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)

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
        return JsonResponse({
            'status': 'Error',
            'description': 'Something went wrong during exporting the datasets',
            'more': str(e)
        }, status=500)

@public
@csrf_exempt
def projects(request):
    if 'API_KEY' not in request.GET:
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)
    elif request.GET.get('API_KEY') != getattr(settings, 'GLOBAL_API_KEY'):
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)
        
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
        return JsonResponse({
            'status': 'Error',
            'description': 'Something went wrong during exporting the projects',
            'more': str(e)
        }, status=500)

@public
@csrf_exempt
def rems_endpoint(request):
    if not getattr(settings, 'REMS_INTEGRATION_ENABLED', False):
        message = f'REMS endpoint called, but it''s disabled.'
        logger.debug(message)
        return JsonResponse({
                'status': 'Error',
                'description': message
            }, status=500)
        
    ip = get_client_ip(request)
    logger.debug(f'REMS endpoint called from: {ip}...')

    allowed_ips = getattr(settings, 'REMS_ALLOWED_IP_ADDRESSES', [])
    skip_check_setting = getattr(settings, 'REMS_SKIP_IP_CHECK', False)
    if '*' in allowed_ips:
        skip_check_setting = True

    if len(allowed_ips) == 0 and not skip_check_setting:
        message = f'REMS - the list of allowed IPs is empty, import failed!'
        logger.debug(message)
        return JsonResponse({
            'status': 'Error',
            'description': message
        }, status=500)

    if ip not in allowed_ips and not skip_check_setting:
        message = f'REMS - the IP is not in the list of allowed IPs, import failed!'
        logger.debug(message)
        return JsonResponse({
            'status': 'Error',
            'description': message
        }, status=500)
    
    try:
        status = "Success" if handle_rems_callback(request) else "Failure"
        logger.debug(f'REMS - import status: {status}!')
        return JsonResponse({'status': f'{status}'}, status=200)
    except Exception as ex:
        message = f'REMS - something went wrong during the import!'
        logger.debug(message)
        return JsonResponse({
            'status': 'Error',
            'description': message,
            'more': str(ex)
        }, status=500)

@public
@csrf_exempt
def permissions(request, user_id: str):
    if 'API_KEY' not in request.GET:
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)
    elif request.GET.get('API_KEY') != getattr(settings, 'GLOBAL_API_KEY'):
        return JsonResponse({
            'status': 'Error',
            'description': 'API_KEY missing or invalid'
        }, status=403)

    try:
        user = User.objects.get(id=user_id)
        return HttpResponse(user.get_access_permissions())
    except Exception as e:
        return JsonResponse({
            'status': 'Error',
            'description': 'Something went wrong during exporting the permissions',
            'more': str(e)
        }, status=500)