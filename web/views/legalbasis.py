from django.http import JsonResponse,  HttpResponse
from django.shortcuts import get_object_or_404 , redirect, render
from django.views.generic import CreateView, UpdateView
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse_lazy

from core.forms import LegalBasisForm
from core.forms.legal_basis import LegalBasisEditForm
from core.models import LegalBasis, Dataset
from core.permissions import permission_required, CheckerMixin
from core.utils import DaisyLogger
from core.constants import Permissions

from web.views.utils import AjaxViewMixin


log = DaisyLogger(__name__)


class LegalBasisCreateView(CheckerMixin, CreateView, AjaxViewMixin):
    model = LegalBasis
    template_name = 'legalbases/legalbasis_form.html'
    form_class = LegalBasisForm
    permission_required = Permissions.EDIT
    permission_target = 'dataset'

    def check_permissions(self, request):
        edited_dataset_pk = request.resolver_match.kwargs['dataset_pk']
        self.permission_object = Dataset.objects.get(pk=edited_dataset_pk)
        super().check_permissions(request)

    def dispatch(self, request, *args, **kwargs):
        """
        Hook method to save related dataset.
        """
        self.dataset = None
        dataset_pk = kwargs.get('dataset_pk')
        if dataset_pk:
            self.dataset = get_object_or_404(Dataset, pk=dataset_pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        if self.dataset:
            self.object.dataset = self.dataset
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, 'Legal basis definition created.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs['dataset'] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})


class LegalBasisEditView(CheckerMixin, UpdateView, AjaxViewMixin):
    model = LegalBasis
    template_name = 'legalbases/legalbasis_form.html'
    form_class = LegalBasisEditForm
    permission_required = Permissions.EDIT
    permission_target = 'dataset'

    def get_permission_object(self):
        obj = super().get_permission_object()
        return obj.dataset

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, 'Legal basis definition updated.')
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy('dataset', kwargs={'pk': self.object.dataset.pk})


@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, 'dataset', (Dataset, 'pk', 'dataset_pk'))
def remove_legalbasis(request, dataset_pk, legalbasis_pk):
    legbasis = get_object_or_404(LegalBasis, pk=legalbasis_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if legbasis.dataset == dataset:
        legbasis.delete()
    return HttpResponse("Legal basis deleted.")
