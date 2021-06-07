from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from core.forms import CohortForm, CohortFormEdit
from core.models import Cohort
from . import facet_view_utils

FACET_FIELDS = settings.FACET_FIELDS['cohort']
from core.models.utils import COMPANY


class CohortCreateView(CreateView):
    model = Cohort
    template_name = 'cohorts/cohort_form.html'
    form_class = CohortForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('cohort', kwargs={'pk': self.object.id})


class CohortDetailView(DetailView):
    model = Cohort
    template_name = 'cohorts/cohort.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = True
        context['can_edit'] = can_edit
        context['company_name'] = COMPANY

        return context


class CohortEditView(UpdateView):
    model = Cohort
    template_name = 'cohorts/cohort_form_edit.html'
    form_class = CohortFormEdit

    def dispatch(self, request, *args, **kwargs):
        the_cohort = Cohort.objects.get(id=kwargs.get('pk'))
        the_user = request.user
        can_edit = True
        if can_edit:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('cohort', kwargs={'pk': self.object.id})


def cohort_list(request):
    query = request.GET.get('query')
    order_by = request.GET.get('order_by')

    cohorts = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Cohort,
        facets=FACET_FIELDS,
        order_by=order_by
    )
    return render(request, 'search/search_page.html', {
        'reset': True,
        'facets': facet_view_utils.filter_empty_facets(cohorts.facet_counts()),
        'query': query or '',
        'title': 'Cohorts',
        'help_text' : Cohort.AppMeta.help_text,
        'search_url': 'cohorts',
        'add_url': 'cohort_add',
        'data': {'cohorts': cohorts},
        'results_template_name': 'search/_items/cohorts.html',
        'company_name': COMPANY,
        'order_by_fields': [
            ('Title', 'title_l'),
        ]
    })


class CohortDelete(DeleteView):
    model = Cohort
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('cohorts')
    success_message = "Cohort was deleted successfully."

    def get_context_data(self, **kwargs):
        context = super(CohortDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'cohort_delete'
        context['id'] = self.object.id
        return context


@staff_member_required
def publish_cohort(request, pk):
    cohort = get_object_or_404(Cohort, pk=pk)
    cohort.is_published = True
    cohort.save()
    return redirect(reverse_lazy('cohort', kwargs={'pk': cohort.id}))


@staff_member_required
def unpublish_cohort(request, pk):
    cohort = get_object_or_404(Cohort, pk=pk)
    cohort.is_published = False
    cohort.save()
    return redirect(reverse_lazy('cohort', kwargs={'pk': cohort.id}))