from django.conf import settings

from excel_response import ExcelResponse

from core.models import Contract, Dataset, Project
from core.utils import DaisyLogger
from . import facet_view_utils

log = DaisyLogger(__name__)


def contracts_export(request):
    query = request.GET.get('query', '')
    order_by = request.GET.get('order_by', '')
    contracts = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Contract,
        facets=settings.FACET_FIELDS['contract'],
        order_by=order_by
    )

    contract_ids = [x.__dict__['pk'] for x in contracts]
    contracts = Contract.objects.filter(id__in=contract_ids)
    return ExcelResponse(contracts)
    
def datasets_export(request):
    query = request.GET.get('query', '')
    order_by = request.GET.get('order_by', '')
    datasets = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Dataset,
        facets=settings.FACET_FIELDS['dataset'],
        order_by=order_by
    )

    dataset_ids = [x.__dict__['pk'] for x in datasets]
    datasets = Dataset.objects.filter(id__in=dataset_ids)
    return ExcelResponse(datasets)

def projects_export(request):
    query = request.GET.get('query', '')
    order_by = request.GET.get('order_by', '')
    projects = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Project,
        facets=settings.FACET_FIELDS['project'],
        order_by=order_by
    )

    project_ids = [x.__dict__['pk'] for x in projects]
    projects = Project.objects.filter(id__in=project_ids)
    return ExcelResponse(projects)
