from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from formtools.wizard.views import NamedUrlSessionWizardView
from django.http import HttpResponseRedirect, Http404
from core.constants import Permissions
from core.forms.storage_location import StorageLocationForm
from core.forms import DatasetForm, DataDeclarationForm, LegalBasisForm, AccessForm
from core.forms.dataset import DatasetFormEdit
from core.models import Dataset, Exposure
from core.models.utils import COMPANY
from core.permissions import CheckerMixin
from core.utils import DaisyLogger
from core.constants import Permissions
from . import facet_view_utils

log = DaisyLogger(__name__)

FACET_FIELDS = settings.FACET_FIELDS['dataset']


class DatasetWizardView(NamedUrlSessionWizardView):
    template_name = "datasets/dataset_wizard_form.html"
    form_list = [
        ("dataset", DatasetForm),
        ("data_declaration", DataDeclarationForm),
        ("storage_location", StorageLocationForm),
        ("legal_basis", LegalBasisForm),
        ("access", AccessForm),
    ]

    def render_done(self, form, **kwargs):
        dataset_id = self.storage.extra_data.get('dataset_id')
        self.storage.reset()
        if dataset_id:
            done_response = HttpResponseRedirect(reverse_lazy('dataset', kwargs={'pk': dataset_id}))
        else:
            done_response = HttpResponseRedirect(reverse_lazy('datasets'))
        return done_response

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        dataset_id = self.storage.extra_data.get('dataset_id', None)
        if dataset_id is not None:
            kwargs['dataset'] = Dataset.objects.get(pk=dataset_id)
        return kwargs

    def process_step(self, form, **kwargs):
        self.storage.extra_data[f'{self.steps.current}-skipped'] = True
        if self.steps.current == 'dataset':
            dataset = form.save()
            self.storage.extra_data['dataset_id'] = dataset.id
            self.storage.extra_data[f'{self.steps.current}-skipped'] = False
        elif form.data.get(f'{self.steps.current}-skip_wizard') != 'True':
            self.storage.extra_data[f'{self.steps.current}-skipped'] = False
            dataset_id = self.storage.extra_data.get('dataset_id')
            try:
                dataset = Dataset.objects.get(pk=dataset_id)
                instance = form.save(commit=False)
                instance.dataset = dataset
                instance.save()
                self.storage.extra_data[f'{self.steps.current}-skipped'] = False
            except Dataset.DoesNotExist:
                raise Http404(f"You need to have a dataset first")
        return self.get_form_step_data(form)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({'step_name': self.steps.current})
        names = [form_key.replace('_', ' ').title() for form_key, _ in self.form_list.items()]
        skips = []
        for step in self.form_list.keys():
            try:
                if self.storage.extra_data[f'{step}-skipped']:
                    skips.append(True)
                else:
                    skips.append(False)
            except KeyError:
                skips.append(False)

        context['steps_verbose_data'] = list(zip(self.form_list, names, skips))
        dataset_id = self.storage.extra_data.get('dataset_id', None)
        if dataset_id is not None:
            context['dataset_id'] = Dataset.objects.get(pk=dataset_id).id
        return context


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
        context['can_see_protected'] = self.request.user.has_permission_on_object(
            f'core.{Permissions.PROTECTED.value}_dataset', self.object)
        context['company_name'] = COMPANY
        context['exposure_list'] = Exposure.objects.filter(dataset=self.object)
        return context


class DatasetEditView(CheckerMixin, UpdateView):
    model = Dataset
    template_name = 'datasets/dataset_form_edit.html'
    form_class = DatasetFormEdit
    permission_required = Permissions.EDIT
    permission_target = 'dataset'

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
        'filters': request.GET.get('filters') or '',
        'order_by': order_by or '',
        'facets': facet_view_utils.filter_empty_facets(datasets.facet_counts()),
        'query': query or '',
        'title': 'Datasets',
        'help_text': Dataset.AppMeta.help_text,
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


class DatasetDelete(CheckerMixin, DeleteView):
    model = Dataset
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('datasets')
    success_message = "Dataset was deleted successfully."
    permission_required = Permissions.DELETE
    permission_target = 'dataset'

    def get_context_data(self, **kwargs):
        context = super(DatasetDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'dataset_delete'
        context['id'] = self.object.id
        return context
    