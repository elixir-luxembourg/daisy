from django.contrib import messages
from django.http import HttpResponse,  JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from django.views.generic import CreateView

from core.forms.storage_location import StorageLocationForm, StorageLocationEditForm
from core.models import Dataset
from core.models.storage_location import DataLocation
from core.permissions import permission_required
from core.constants import Permissions
from web.views.utils import AjaxViewMixin
from core.utils import DaisyLogger


log = DaisyLogger(__name__)

@permission_required(Permissions.EDIT, (Dataset, 'pk', 'dataset_pk'))
def edit_storagelocation(request, pk, dataset_pk):
    loc = get_object_or_404(DataLocation, pk=pk)
    if request.method == 'POST':
        form = StorageLocationEditForm(request.POST,  request.FILES, instance=loc)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Storage location definition updated")
            redirecturl = reverse_lazy('dataset', kwargs={'pk': dataset_pk})
            return redirect(to=redirecturl)
        else:
            return JsonResponse(
                {'error':
                     {'type': 'Edit error', 'messages': [str(e) for e in form.errors]
                      }}, status=405)
    else:
        form = StorageLocationEditForm(instance=loc)

    log.debug(submit_url=request.get_full_path())
    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path() })



class StorageLocationCreateView(CreateView, AjaxViewMixin):
    model = DataLocation
    template_name = 'storage_locations/storage_location_form.html'
    form_class = StorageLocationForm

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
        self.object.dataset = self.dataset
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "Storage definition created")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs['dataset'] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})

@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, (Dataset, 'pk', 'dataset_pk'))
def remove_storagelocation(request, dataset_pk, storagelocation_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    datalocation = get_object_or_404(DataLocation, pk=storagelocation_pk)
    if datalocation.dataset == dataset:
        datalocation.delete()
    messages.add_message(request, messages.SUCCESS, 'Storage location deleted.')
    return HttpResponse("Storage location deleted")
