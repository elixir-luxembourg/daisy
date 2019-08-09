from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from core.forms import PartnerForm
from core.forms.partner import PartnerFormEdit
from core.models import Partner
from reversion.views import RevisionMixin, create_revision
from sequences import get_next_value

from web.views.utils import AjaxViewMixin
from core.permissions import permission_required
from core.models.utils import COMPANY
from . import facet_view_utils

FACET_FIELDS = settings.FACET_FIELDS['partner']

class PartnerCreateView(RevisionMixin, CreateView, AjaxViewMixin):
    model = Partner
    template_name = 'partners/partner_form.html'
    form_class = PartnerForm

    def get_initial(self):
        initial = super().get_initial()

        initial.update({'elu_accession': '-', 'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('partners')


class PartnerListView(ListView):
    model = Partner
    template_name = 'partners/partner_list.html'


class PartnerDetailView(DetailView):
    model = Partner
    template_name = 'partners/partner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_edit = True
        context['can_edit'] = can_edit
        context['company_name'] = COMPANY

        return context


class PartnerEditView(RevisionMixin, UpdateView):
    model = Partner
    template_name = 'partners/partner_form_edit.html'
    form_class = PartnerFormEdit

    def dispatch(self, request, *args, **kwargs):
        the_partner = Partner.objects.get(id=kwargs.get('pk'))
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
        return reverse_lazy('partner', kwargs={'pk': self.object.id})


def partner_search_view(request):
    query = request.GET.get('query')
    order_by = request.GET.get('order_by')
    partners = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Partner,
        facets=FACET_FIELDS,
        order_by=order_by
    )
    return render(request, 'search/search_page.html', {
        'reset': True,
        'facets': facet_view_utils.filter_empty_facets(partners.facet_counts()),
        'query': query or '',
        'title': 'Partners',
        'help_text' : Partner.AppMeta.help_text,
        'search_url': 'partners',
        'add_url': 'partner_add',
        'data': {'partners': partners},
        'results_template_name': 'search/_items/partners.html',
        'company_name': COMPANY,
        'order_by_fields': [
            ('Name', 'name'),
        ]
    })


def generate_elu_accession():
    elu_accession = 'ELU_I_' + str(get_next_value('elu_accession', initial_value=100))
    return elu_accession

@create_revision
def publish_partner(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if not partner.is_published:
        partner.is_published = True
        if partner.elu_accession == '-':
            partner.elu_accession = generate_elu_accession()
    else:
        partner.is_published = False
    partner.save(update_fields=['is_published', 'elu_accession'])
    return HttpResponseRedirect(reverse_lazy('partner', kwargs={'pk': pk}))


class PartnerDelete(RevisionMixin, DeleteView):
    model = Partner
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('partners')
    success_message = "Partner was deleted successfully."

    def get_context_data(self, **kwargs):
        context = super(PartnerDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'partner_delete'
        context['id'] = self.object.id
        return context
