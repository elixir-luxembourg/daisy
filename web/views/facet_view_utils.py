from collections import defaultdict

from django.db.models import Q

from haystack.inputs import Exact, AutoQuery
from haystack.query import SearchQuerySet

from core.utils import DaisyLogger

log = DaisyLogger(__name__)

"""
Utility method to rapidly build a facetted view of a search index.
"""


def _filter_facets(facets):
    """
    Filter facets that are empty or that all terms have 0 results
    """
    fields = facets.get("fields", {})
    filtered = {}
    for item, values in fields.items():
        for term, count in values:
            if count > 0:
                filtered[item] = values
                break
    facets["fields"] = filtered
    return facets


def _filter_query_to_search_parameters(request, filters):
    """
    Transform the query dict list from the facet field parameter to a dict containing parameters, e.g:
    ['project_title:Test project2', 'study_title:s5', 'study_title:s1']
    to
    {'project_title': ['Test project2'], 'study_title': ['s5', 's1']}
    """
    parameters = defaultdict(list)
    for element in filters:
        name, *value = element.split(":")
        value = ":".join(value)
        parameters[name].append(value)
    return parameters


def _search_objects(query, filters, facets, model_object, order_by=None):
    """
    Search objects via solR.
    query: the user search query
    filters: list containing filters
    facets: the list of facets
    model_object: the model the search is refering to
    If a filter key is repeated, we apply a OR lookup.
    return a queryset
    """
    log.debug(
        "search_objects",
        query=query,
        filter=filters,
        facets=facets,
        model_object=model_object,
        order_by=order_by,
    )
    # start queryset
    queryset = SearchQuerySet().models(
        model_object
    )  # .narrow("namespace:(%s)" % namespace.name)
    # filter by facets filters
    for key, values in filters.items():
        tmp = None
        if isinstance(values, (list, tuple)):
            # apply OR lookup if same key is repeated.
            for value in values:
                if tmp is None:
                    tmp = Q(**{key: Exact(value)})
                else:
                    tmp &= Q(**{key: Exact(value)})
        else:
            # only one value, no need to loop.
            tmp = Q(**{key: Exact(values)})
        queryset = queryset.filter(tmp)

    # execute the query
    if query:
        queryset = queryset.filter(content=AutoQuery(query))
    # get facets
    if facets:
        for field in facets:
            queryset = queryset.facet(field)
    # apply order_by if any
    if order_by:
        queryset = queryset.order_by(order_by)
    return queryset


def filter_empty_facets(facets):
    """
    Filter facets that are empty or that all terms have 0 results.
    facets: the facets_counts() result from the search result
    """
    fields = facets.get("fields", {})
    filtered = {}
    for item, values in fields.items():
        for term, count in values:
            if count > 0:
                filtered[item] = values
                break
    facets["fields"] = filtered
    return facets


def search_objects(request, filters, query, object_model, facets, order_by=None):
    """
    Search objects on the indexer (solR)
    filters: filters parameters
    query: the user search
    object_model: which index model to search
    facets: which facetting to apply
    """
    filters = _filter_query_to_search_parameters(request, filters)
    return _search_objects(query, filters, facets, object_model, order_by=order_by)
