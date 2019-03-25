from core.forms.access import AccessForm
from web.views.utils import AjaxViewMixin
from django.views.generic import CreateView, DetailView
from core.models import Access, Dataset
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from core.permissions import permission_required
from django.views.decorators.http import require_http_methods

class AccessCreateView(CreateView, AjaxViewMixin):
    model = Access
    template_name = 'accesses/access_form.html'
    form_class = AccessForm

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
        messages.add_message(self.request, messages.SUCCESS, "Access created")
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


class AccessDetailView(DetailView):
    model = Access
    template_name = 'accesses/access.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        the_user = self.request.user
        can_edit = the_user.can_edit_dataset(self.object.dataset)
        context['can_edit'] = can_edit
        return context

@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def remove_access(request, dataset_pk, access_pk):
    access = get_object_or_404(Access, pk=access_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if access.dataset == dataset:
        access.delete()
    return HttpResponse("Access unlinked")