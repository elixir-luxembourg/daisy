from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin

from core.forms.exposure import ExposureForm, ExposureEditForm, ExposureRemoveForm
from core.models import Dataset, Exposure
from core.utils import DaisyLogger

from web.views.utils import AjaxViewMixin, can_publish, get_rems_forms

log = DaisyLogger(__name__)


class DataStewardGroupRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return can_publish(self.request.user)


class ExposureCreateView(DataStewardGroupRequiredMixin, CreateView, AjaxViewMixin):
    model = Exposure
    form_class = ExposureForm

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
        """If the form is valid, save the associated model and add to the exposure"""
        self.object = form.save(commit=False)
        self.object.dataset = self.dataset
        rems_forms_dict = get_rems_forms(self.object.form_id)
        self.object.form_name = rems_forms_dict["form/internal-name"]
        self.object.save()
        messages.add_message(
            self.request, messages.SUCCESS, "exposure endpoint created"
        )
        # generate elu accession for dataset & publish subentities
        self.dataset.publish()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs["dataset"] = self.dataset
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy("dataset", kwargs={"pk": self.dataset.pk})


class ExposureEditView(DataStewardGroupRequiredMixin, UpdateView, AjaxViewMixin):
    model = Exposure
    form_class = ExposureEditForm

    def dispatch(self, request, *args, **kwargs):
        """
        Hook method to save related dataset and endpoint.
        """
        self.dataset = None
        dataset_pk = kwargs.get("dataset_pk")
        if dataset_pk:
            self.dataset = get_object_or_404(Dataset, pk=dataset_pk)

        self.endpoint = None
        exposure_pk = kwargs.get("pk")
        if exposure_pk:
            self.endpoint = get_object_or_404(Exposure, pk=exposure_pk).endpoint

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.dataset:
            kwargs["dataset"] = self.dataset
        if self.endpoint:
            kwargs["endpoint"] = self.endpoint
        return kwargs

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the exposure"""
        self.object = form.save(commit=False)
        rems_forms_dict = get_rems_forms(self.object.form_id)
        self.object.form_name = rems_forms_dict["form/internal-name"]
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "Exposure record updated")
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        if self.object.dataset:
            return reverse_lazy("dataset", kwargs={"pk": self.object.dataset.pk})
        return super().get_success_url()


class ExposureRemoveView(DataStewardGroupRequiredMixin, UpdateView, AjaxViewMixin):
    model = Exposure
    form_class = ExposureRemoveForm

    def get_object(self, queryset=None):
        return get_object_or_404(
            Exposure,
            pk=self.kwargs.get("pk"),
            dataset__pk=self.kwargs.get("dataset_pk"),
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.dataset = self.object.dataset
        self.endpoint = self.object.endpoint
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy("dataset", kwargs={"pk": self.dataset.pk})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.delete(deprecation_reason=form.cleaned_data["deprecation_reason"])
        messages.add_message(
            self.request, messages.SUCCESS, "Exposure record deprecated"
        )
        return super().form_valid(form)


@require_http_methods(["DELETE"])
@user_passes_test(can_publish)
def remove_exposure(request, dataset_pk, exposure_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    exposure = get_object_or_404(Exposure, pk=exposure_pk)
    if exposure.dataset == dataset:
        exposure.delete()
    if len(dataset.exposures.all()) < 1:
        # needed to trigger reindex of dataset and changing dataset.is_published to false
        dataset.save()
    messages.add_message(request, messages.SUCCESS, "exposure record deleted.")
    return HttpResponse("exposure deleted")
