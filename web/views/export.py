from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

from excel_response import ExcelResponse

from core.models import Cohort, Contact, Contract, Dataset, Partner, Project
from core.utils import DaisyLogger
from . import facet_view_utils

log = DaisyLogger(__name__)


@staff_member_required
def generic_export(request, object_class, object_name):
    query = request.GET.get('query', '')
    order_by = request.GET.get('order_by', '')
    objects = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=object_class,
        facets=settings.FACET_FIELDS[object_name],
        order_by=order_by
    )

    objects_ids = [x.__dict__['pk'] for x in objects]
    objects = object_class.objects.filter(id__in=objects_ids)
    values = [x.serialize_to_export() for x in objects]
    return ExcelResponse(values)

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
