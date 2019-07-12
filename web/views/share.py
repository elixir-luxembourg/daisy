from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, UpdateView

from core.forms.share import ShareForm, shareFormFactory, ShareFormEdit
from core.models import Share, Dataset, Partner
from core.permissions import permission_required
from web.views.utils import AjaxViewMixin

class ShareEditView(UpdateView):
    model = Share
    template_name = 'shares/share_form_edit.html'
    form_class = ShareFormEdit

    def get_success_url(self):
        return reverse_lazy('dataset', kwargs={'pk': self.object.dataset.id})


class ShareDetailView(DetailView):
    model = Share
    template_name = 'shares/share.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        the_user = self.request.user
        can_edit = the_user.can_edit_dataset(self.object.dataset)
        context['can_edit'] = can_edit
        return context


class ShareCreateView(CreateView, AjaxViewMixin):
    model = Share
    template_name = 'shares/share_form.html'
    form_class = ShareForm

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
        messages.add_message(self.request, messages.SUCCESS, "Share created")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        partner = self.request.GET.get('partner', None)
        if partner is not None:
            partner = get_object_or_404(Partner, pk=int(partner))
        return shareFormFactory(partner=partner, dataset=self.dataset, **self.get_form_kwargs())

    def get_success_url(self, **kwargs):
        if self.dataset:
            return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})
        return super().get_success_url()


@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def remove_share(request, dataset_pk, share_pk):
    share = get_object_or_404(Share, pk=share_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if share.dataset == dataset:
        share.delete()
    return HttpResponse("Share deleted")


