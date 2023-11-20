from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView

from core.forms.storage_location import StorageLocationForm, StorageLocationEditForm
from core.models import Dataset
from core.models.storage_location import DataLocation
from core.permissions import permission_required, CheckerMixin
from core.constants import Permissions
from core.utils import DaisyLogger

from web.views.utils import AjaxViewMixin


log = DaisyLogger(__name__)


class StorageLocationCreateView(CheckerMixin, CreateView, AjaxViewMixin):
    model = DataLocation
    template_name = "storage_locations/storage_location_form.html"
    form_class = StorageLocationForm
    permission_required = Permissions.EDIT
    permission_target = "dataset"

    def check_permissions(self, request):
        parent_dataset_pk = request.resolver_match.kwargs["dataset_pk"]
        self.permission_object = Dataset.objects.get(pk=parent_dataset_pk)
        super().check_permissions(request)

    def dispatch(self, request, *args, **kwargs):
        """
        Hook method to save related dataset.
        """
        self.dataset = None
        dataset_pk = kwargs.get("dataset_pk")
        if dataset_pk:
            self.dataset = get_object_or_404(Dataset, pk=dataset_pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.dataset = self.dataset
        self.object.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Storage definition created"
        )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs["dataset"] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy("dataset", kwargs={"pk": self.dataset.pk})


class StorageLocationEditView(CheckerMixin, UpdateView, AjaxViewMixin):
    model = DataLocation
    form_class = StorageLocationEditForm
    template_name = "storage_locations/storage_location_form.html"
    permission_required = Permissions.EDIT
    permission_target = "dataset"

    def get_permission_object(self, queryset=None):
        obj = super().get_permission_object()
        log.debug(obj)
        return obj.dataset

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Storage definition updated"
        )
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        if self.object.dataset:
            return reverse_lazy("dataset", kwargs={"pk": self.object.dataset.pk})
        return super().get_success_url()


@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, "dataset", (Dataset, "pk", "dataset_pk"))
def remove_storagelocation(request, dataset_pk, storagelocation_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    datalocation = get_object_or_404(DataLocation, pk=storagelocation_pk)
    if datalocation.dataset == dataset:
        datalocation.delete()
    messages.add_message(request, messages.SUCCESS, "Storage location deleted.")
    return HttpResponse("Storage location deleted")
