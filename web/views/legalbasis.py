import os

from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404 , redirect, render
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse_lazy
from core.forms import LegalBasisForm
from core.forms.legal_basis import LegalBasisEditForm
from core.models import LegalBasis, Dataset
from core.permissions import permission_required_from_content_type, permission_required
from core.utils import DaisyLogger
from web.views.utils import AjaxViewMixin

log = DaisyLogger(__name__)


class LegalBasisCreateView(CreateView, AjaxViewMixin):
    model = LegalBasis
    template_name = 'legalbases/legalbasis_form.html'
    form_class = LegalBasisForm

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
        messages.add_message(self.request, messages.SUCCESS, "Legal basis definition created")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs['dataset'] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        if self.dataset:
            return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})
        return super().get_success_url()

class LegalBasisCreateView(CreateView, AjaxViewMixin):
    model = LegalBasis
    template_name = 'legalbases/legalbasis_form.html'
    form_class = LegalBasisForm

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
        messages.add_message(self.request, messages.SUCCESS, "Legal basis definition created")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs['dataset'] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        if self.dataset:
            return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})
        return super().get_success_url()


def edit_legalbasis(request, pk, dataset_pk):
    # log.debug('editing legal basis', post=request.POST)
    legalbasis = get_object_or_404(LegalBasis, pk=pk)
    if request.method == 'POST':
        form = LegalBasisEditForm(request.POST,  request.FILES, instance=legalbasis)
        if form.is_valid():
            # data = form.cleaned_data
            form.save()
            messages.add_message(request, messages.SUCCESS, "Legal basis updated")
            redirecturl = reverse_lazy('dataset', kwargs={'pk': dataset_pk})
            return redirect(to=redirecturl, pk=legalbasis.id)
        else:
            return JsonResponse(
                {'error':
                     {'type': 'Edit error', 'messages': [str(e) for e in form.errors]
                      }}, status=405)
    else:
        form = LegalBasisEditForm(instance=legalbasis)

    log.debug(submit_url=request.get_full_path())
    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path() })

@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def remove_legalbasis(request, dataset_pk, legalbasis_pk):
    legbasis = get_object_or_404(LegalBasis, pk=legalbasis_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if legbasis.dataset == dataset:
        legbasis.delete()
    return HttpResponse("Legal basis deleted")
