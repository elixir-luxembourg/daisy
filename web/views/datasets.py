from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from core.forms import DatasetForm
from core.forms.dataset import DatasetFormEdit
from core.forms.share import shareFormFactory
from core.forms.storage_location import dataLocationFormFactory
from core.models import Dataset, Partner
from core.models.utils import COMPANY
from core.permissions import permission_required, CheckerMixin, constants
from core.utils import DaisyLogger
from . import facet_view_utils

log = DaisyLogger(__name__)

FACET_FIELDS = settings.FACET_FIELDS['dataset']

class DatasetCreateView(CreateView):
    model = Dataset
    template_name = 'datasets/dataset_form.html'
    form_class = DatasetForm

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.kwargs.get('pk')
        initial.update({'user': self.request.user})
        if project_id:
            initial.update({'project': project_id})
        return initial

    def get_success_url(self):
        return reverse_lazy('dataset', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        #  assign permissions to the user
        self.request.user.assign_permissions_to_dataset(form.instance)

        # assign also permissions to the people that are responsible
        for local_custodian in form.instance.local_custodians.all():
            local_custodian.assign_permissions_to_dataset(form.instance)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class DatasetDetailView(DetailView):
    model = Dataset
    template_name = 'datasets/dataset.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_admin_of_dataset(self.object)
        context['can_edit'] = self.request.user.can_edit_dataset(self.object)
        context['company_name'] = COMPANY
        return context


class DatasetEditView(CheckerMixin, UpdateView):
    model = Dataset
    template_name = 'datasets/dataset_form_edit.html'
    form_class = DatasetFormEdit
    permission_required = constants.Permissions.EDIT


    def get_initial(self):
        initial = super().get_initial()
        project_id = self.object.project.id if self.object.project else None
        initial.update({'user': self.request.user, 'project': project_id})
        return initial

    def get_success_url(self):
        return reverse_lazy('dataset', kwargs={'pk': self.object.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'dataset': self.object})
        return kwargs


def dataset_list(request):
    query = request.GET.get('query')
    order_by = request.GET.get('order_by')
    datasets = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Dataset,
        facets=FACET_FIELDS,
        order_by=order_by
    )
    return render(request, 'search/search_page.html', {
        'reset': True,
        'facets': facet_view_utils.filter_empty_facets(datasets.facet_counts()),
        'query': query or '',
        'title': 'Datasets',
        'help_text' : Dataset.AppMeta.help_text,
        'search_url': 'datasets',
        'add_url': 'dataset_add',
        'data': {'datasets': datasets},
        'results_template_name': 'search/_items/datasets.html',
        'company_name': COMPANY,
        'order_by_fields': [
            ('Title', 'title_l'),
            ('Embargo date', 'embargo_date'),
            ('End of storage duration', 'end_of_storage_duration')
        ]
    })


class DatasetDelete(DeleteView):
    model = Dataset
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('datasets')
    success_message = "Dataset was deleted successfully."

    def get_context_data(self, **kwargs):
        context = super(DatasetDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'dataset_delete'
        context['id'] = self.object.id
        return context


## COLLABORATION METHODS ##
#
# @permission_required('EDIT', (Dataset, 'pk', 'pk'))
# def dataset_contract_add(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     if request.method == 'GET':
#         form = ContractSelection(dataset=dataset)
#         return render(request, 'modal_form.html', {
#             'dataset': dataset,
#             'form': form,
#             'submit_url': request.get_full_path(),
#         })
#     if request.method == 'POST':
#         form = ContractSelection(request.POST, dataset=dataset)
#         if form.is_valid():
#             try:
#                 contract = form.cleaned_data['contract']
#             except IntegrityError as e:
#                 messages.add_message(request, messages.ERROR, e)
#                 return redirect('dataset', pk=dataset.pk)
#
#             messages.add_message(request, messages.SUCCESS, 'Dataset added')
#             return redirect('dataset', pk=dataset.pk)
#         return render(request, 'modal_form.html', {
#             'dataset': dataset,
#             'form': form,
#             'submit_url': request.get_full_path(),
#         })
#
#
# @permission_required('EDIT', (Dataset, 'pk', 'pk'))
# @permission_required('DELETE', (Contract, 'pk', 'cid'))
# def dataset_contract_remove(request, pk, cid):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     contract = get_object_or_404(Contract, pk=cid)
#     messages.add_message(request, messages.SUCCESS, 'Contract removed.')
#     return HttpResponse("Contract deleted")
#
#
# @permission_required('EDIT', (Dataset, 'pk', 'pk'))
# def dataset_dataset_link(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     if request.method == 'GET':
#         form = DatasetSelection(dataset=dataset)
#         return render(request, 'modal_form.html', {
#             'dataset': dataset,
#             'form': form,
#             'submit_url': request.get_full_path(),
#         })
#     if request.method == 'POST':
#         form = DatasetSelection(request.POST, dataset=dataset)
#         if form.is_valid():
#             used = form.cleaned_data['dataset']
#             try:
#                 pass
#             except IntegrityError as e:
#                 messages.add_message(request, messages.ERROR, e)
#                 return redirect('dataset', pk=dataset.pk)
#             messages.add_message(request, messages.SUCCESS, 'Datasets linked')
#             return redirect('dataset', pk=dataset.pk)
#         return render(request, 'modal_form.html', {
#             'dataset': dataset,
#             'form': form,
#             'submit_url': request.get_full_path(),
#         })
#
#
# @permission_required('EDIT', (Dataset, 'pk', 'target_id'))
# def dataset_dataset_unlink(request, target_id, used_id):
#     target = get_object_or_404(Dataset, pk=target_id)
#     used = get_object_or_404(Dataset, pk=used_id)
#     messages.add_message(request, messages.SUCCESS, 'Link removed.')
#     return HttpResponse("ink deleted")


# @permission_required('EDIT', (Dataset, 'pk', 'pk'))
# def dataset_data_add(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     if request.method == 'GET':
#         backend = request.GET.get('backend', None)
#         if backend is not None:
#             backend = get_object_or_404(StorageResource, pk=int(backend))
#         form = dataLocationFormFactory(backend=backend)
#         return render(request, 'modal_form.html', {
#             'dataset': dataset,
#             'form': form,
#             'submit_url': request.get_full_path(),
#         })
#     if request.method == 'POST':
#         backend = request.POST.get('backend', None)
#         if backend is not None:
#             backend = get_object_or_404(StorageResource, pk=int(backend))
#             form = dataLocationFormFactory(request.POST, backend=backend)
#             if form.is_valid():
#                 datalocation = form.save()
#                 dataset.data.add(datalocation)
#                 messages.add_message(request, messages.SUCCESS, 'File added')
#                 return redirect('dataset', pk=dataset.pk)
#             return render(request, 'modal_form.html', {
#                 'dataset': dataset,
#                 'form': form,
#                 'submit_url': request.get_full_path(),
#             })
#         messages.add_message(request, messages.ERROR, 'No valid backend detected.')
#         return redirect('dataset', pk=dataset.pk)


@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def dataset_share_add(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    if request.method == 'GET':
        partner = request.GET.get('partner', None)
        if partner is not None:
            partner = get_object_or_404(Partner, pk=int(partner))
        form = dataLocationFormFactory(partner=partner)
        return render(request, 'modal_form.html', {
            'dataset': dataset,
            'form': form,
            'submit_url': request.get_full_path(),
        })
    if request.method == 'POST':
        partner = request.POST.get('partner', None)
        if partner is not None:
            partner = get_object_or_404(Partner, pk=int(partner))
            form = shareFormFactory(request.POST, partner=partner)
            if form.is_valid():
                share = form.save()
                dataset.shares.add(share)
                messages.add_message(request, messages.SUCCESS, 'New share added')
                return redirect('dataset', pk=dataset.pk)
            return render(request, 'modal_form.html', {
                'dataset': dataset,
                'form': form,
                'submit_url': request.get_full_path(),
            })
        messages.add_message(request, messages.ERROR, 'No valid partner detected.')
        return redirect('dataset', pk=dataset.pk)
