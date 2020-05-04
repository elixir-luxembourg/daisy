from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from excel_response import ExcelResponse

from core.models import Cohort, Contact, Contract, Dataset, Partner, Project
from core.utils import DaisyLogger
from . import facet_view_utils

log = DaisyLogger(__name__)


@staff_member_required
def generic_export(request, object_model_class, object_name):
    def _do_export(request, object_model_class, object_name):
        query = request.GET.get('query', '')
        order_by = request.GET.get('order_by', '')
        objects = facet_view_utils.search_objects(
            request,
            filters=request.GET.getlist('filters'),
            query=query,
            object_model=object_model_class,
            facets=settings.FACET_FIELDS[object_name],
            order_by=order_by
        )

        objects_ids = [obj.__dict__['pk'] for obj in objects]
        objects = object_model_class.objects.filter(id__in=objects_ids)
        values = [obj.serialize_to_export() for obj in objects]

        if len(values) == 0:
            raise ValueError("There are no values to export - your selection was empty")
        return ExcelResponse(values)
    
    try:
        response = _do_export(request, object_model_class, object_name)
        return response
    except Exception as e:
        return HttpResponse(f'There was a problem with export: \r\n{str(e)}')

def cohorts_export(request):
    return generic_export(request, Cohort, 'cohort')

def contacts_export(request):
    return generic_export(request, Contact, 'contact')

def contracts_export(request):
    return generic_export(request, Contract, 'contract')
    
def datasets_export(request):
    return generic_export(request, Dataset, 'dataset')

def partners_export(request):
    return generic_export(request, Partner, 'partner')

def projects_export(request):
    return generic_export(request, Project, 'project')
