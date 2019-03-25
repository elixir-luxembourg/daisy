import json
import os

from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest

from stronghold.decorators import public

from core.models import User, Cohort, Partner, DiseaseTerm
from core.models.term_model import TermCategory, PhenotypeTerm, StudyTerm, GeneTerm
from elixir_daisy import settings
from ontobio import obograph_util, Ontology


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
def cohorts(request):
    return JsonResponse({
        "results": [cohort.to_dict() for cohort in Cohort.objects.all()]
    })

@public
def partners(request):
    return JsonResponse({
        "results": [partner.to_dict() for partner in Partner.objects.all()]
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
