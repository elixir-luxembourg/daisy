from django.contrib import messages
from django.contrib.messages import add_message
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, ListView, DetailView, UpdateView

from core.forms import StorageLocationForm, PickStorageLocationForm
from core.forms.storage_location import dataLocationFormFactory
from core.models import Dataset
from core.models.storage_location import DataLocation
from core.models.storage_resource import StorageResource
from core.permissions import permission_required
from web.views.utils import AjaxViewMixin


@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def remove_storage_location_from_dataset(request, pk, storage_location_id):
    storage_location = get_object_or_404(DataLocation, pk=storage_location_id)
    dataset = get_object_or_404(Dataset, pk=pk)
    dataset.data_locations.remove(storage_location)
    return HttpResponse("Storage location unlinked")


@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def pick_storage_location_for_dataset(request, pk):
    if request.method == 'POST':
        form = PickStorageLocationForm(request.POST)
        if form.is_valid():
            dataset = get_object_or_404(Dataset, pk=pk)
            storage_location_id = form.cleaned_data['data_file']
            storage_location = get_object_or_404(DataLocation, pk=storage_location_id)
            dataset.data_locations.add(storage_location)
        else:
            return HttpResponseBadRequest("wrong parameters")
        dataset.save()
        add_message(request, messages.SUCCESS, "Data file added")
        return redirect(to='dataset', pk=pk)

    else:
        form = PickStorageLocationForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def add_storage_location_to_dataset(request, pk):
    if request.method == 'POST':
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            dataset = get_object_or_404(Dataset, pk=pk)
            storage_location = form.save()
            dataset.data_locations.add(storage_location)
            dataset.save()
            add_message(request, messages.SUCCESS, "Data file added")
        else:
            error_messages = []
            for field, error in form.errors.items():
                error_message = "{}: {}".format(field, error[0])
                error_messages.append(error_message)
            add_message(request, messages.ERROR, "\n".join(error_messages))
        return redirect(to='dataset', pk=pk)

    else:
        form = StorageLocationForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


class StorageLocationCreateView(CreateView):
    model = DataLocation
    template_name = 'storage_locations/storage_location_form.html'
    form_class = StorageLocationForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('storage_locations')

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class StorageLocationListView(ListView):
    model = DataLocation
    template_name = 'storage_locations/storage_locations_list.html'


class StorageLocationDetailView(DetailView):
    model = DataLocation
    template_name = 'storage_locations/storage_location.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class StorageLocationEditView(UpdateView):
    model = DataLocation
    template_name = 'storage_locations/storage_location_form_edit.html'
    form_class = StorageLocationForm

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def get_success_url(self):
        return reverse_lazy('storage_location', kwargs={'pk': self.object.id})


class DataLocationCreateView(CreateView, AjaxViewMixin):
    model = DataLocation
    template_name = 'storage_locations/storage_location_form.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Hook method to save related dataset.
        """
        self.dataset = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.dataset = self.dataset
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "Datafile created")
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy('dataset', kwargs={'pk': self.dataset.pk})

    def get_form(self, form_class=None):
        backend = self.request.GET.get('backend', None)
        if backend is not None:
            backend = get_object_or_404(StorageResource, pk=int(backend))
        return dataLocationFormFactory(backend=backend, dataset=self.dataset, **self.get_form_kwargs())


class DataLocationDetailView(DetailView):
    model = DataLocation
    template_name = 'storage_locations/data_location.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = context['object'].cast()
        return context


@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def datalocation_remove(request, dataset_pk, data_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    datalocation = get_object_or_404(DataLocation, pk=data_pk)
    if datalocation.dataset == dataset:
        datalocation.delete()
    messages.add_message(request, messages.SUCCESS, 'Data file removed.')
    return HttpResponse("Data file deleted")
