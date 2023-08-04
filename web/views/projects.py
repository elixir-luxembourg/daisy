from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from core.constants import Permissions, Groups
from core.forms.contract import ContractForm
from core.forms.dataset import DatasetForm
from core.forms.project import ProjectForm, DatasetSelection
from core.models import Project, Contract
from core.permissions import permission_required
from core.permissions.checker import CheckerMixin
from web.views.utils import is_data_steward
from . import facet_view_utils

FACET_FIELDS = settings.FACET_FIELDS['project']
from core.models.utils import COMPANY
from django.urls import reverse

class ProjectListView(ListView):
    model = Project
    # template_name = 'projects/project_list.html'


def project_list(request):
    query = request.GET.get('query')
    order_by = request.GET.get('order_by')
    projects = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist('filters'),
        query=query,
        object_model=Project,
        facets=FACET_FIELDS,
        order_by=order_by
    )
    return render(request, 'search/search_page.html', {
        'reset': True,
        'facets': facet_view_utils.filter_empty_facets(projects.facet_counts()),
        'query': query or '',
        'filters': request.GET.get('filters') or '',
        'order_by': order_by or '',
        'title': 'Projects',
        'help_text': Project.AppMeta.help_text,
        'search_url': 'projects',
        'add_url': 'project_add',
        'data': {'projects': projects},
        'results_template_name': 'search/_items/projects.html',
        'company_name': COMPANY,
        'order_by_fields': [
            ('Acronym', 'acronym_l'),
            ('Start date', 'start_date'),
            ('Title', 'title_l')
        ]
    })


class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_form_kwargs(self):
        # get user from kwargs and check if user is pi or not
        # automatically add him to the responsible people if pi
        kwargs = super().get_form_kwargs()
        if self.request.user.is_part_of(Groups.VIP) and 'data' in kwargs:
            data = kwargs['data'].copy()
            if 'local_custodians' not in data or str(self.request.user.pk) not in data['local_custodians']:
                data.update({'local_custodians': str(self.request.user.pk)})
            kwargs.update({'data': data})
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.add_message(self.request, messages.SUCCESS, "Project created")
        if form.instance.legal_documents.all().count() == 0:
            messages.add_message(self.request, messages.INFO,
                                 "Project has no document attachments, please upload documents.")

        # assign perm to user
        self.request.user.assign_permissions_to_project(form.instance)

        # assign perm to responsible peoples
        for local_custodian in form.instance.local_custodians.all():
            local_custodian.assign_permissions_to_project(form.instance)

        return response

    def get_success_url(self):
        return reverse_lazy('project', kwargs={'pk': self.object.id})


class ProjectDetailView(DetailView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_admin_of_project(self.object)
        context['can_edit'] = self.request.user.can_edit_project(self.object)
        context['company_name'] = COMPANY
        pk = ContentType.objects.get(model='project').pk
        context['content_type'] = pk
        context['content_type_name'] = 'project'
        context['object_id'] = self.object.pk
        context['datafiles'] = [d for d in self.object.legal_documents.all()]

        return context


class ProjectEditView(CheckerMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form_edit.html'

    permission_required = Permissions.EDIT
    permission_target = 'project'

    def get_success_url(self):
        return reverse_lazy('project', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.add_message(self.request, messages.SUCCESS, "Project updated")
        if form.instance.legal_documents.all().count() == 0:
            messages.add_message(self.request, messages.INFO,
                                 "Project has no document attachments, please upload documents.")
        return response


## DATASET METHODS ##

@permission_required(Permissions.EDIT, 'project', (Project, 'pk', 'pk'))
def project_dataset_create(request, pk, flag):
    project = get_object_or_404(Project, pk=pk)

    # render the form
    if request.method == 'GET':
        form = DatasetForm()
        return render(request, 'projects/create_dataset.html', {
            'project': project,
            'form': form,
        })
    # try to attach the dataset to the project
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                try:
                    dataset = form.save()
                except IntegrityError as e:
                    messages.add_message(request, messages.ERROR, e)
                    return redirect('project', pk=project.pk)

            messages.add_message(request, messages.SUCCESS, 'Dataset created')
            return redirect('project', pk=project.pk)
        return render(request, 'projects/create_dataset.html', {
            'project': project,
            'form': form,
        })


@permission_required(Permissions.EDIT, 'project', (Project, 'pk', 'pk'))
def project_dataset_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'GET':
        form = DatasetSelection()
        return render(request, 'projects/add_dataset.html', {
            'project': project,
            'form': form,
        })
    if request.method == 'POST':
        form = DatasetSelection(request.POST)
        if form.is_valid():
            try:
                dataset = form.cleaned_data['dataset']
            except IntegrityError as e:
                messages.add_message(request, messages.ERROR, e)
                return redirect('project', pk=project.pk)

            messages.add_message(request, messages.SUCCESS, 'Dataset added')
            return redirect('project', pk=project.pk)
        return render(request, 'projects/add_dataset.html', {
            'project': project,
            'form': form,
        })


@permission_required(Permissions.EDIT, 'project', (Project, 'pk', 'pk'))
def project_dataset_choose_type(request, pk):
    """
    View to choose dataset type to create
    """
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/choose_dataset_type.html', {
        'project': project,
    })


# CONTRACTS METHODS


@permission_required(Permissions.EDIT, 'project', (Project, 'pk', 'pk'))
def project_contract_create(request, pk):
    project = get_object_or_404(Project, pk=pk)
    # get the correct form from the flag selected
    # render the form
    if request.method == 'GET':
        form = ContractForm(show_project=False)
        return render(request, 'projects/create_contract.html', {
            'project': project,
            'form': form,
        })
    # try to attach the dataset to the project
    if request.method == 'POST':
        form = ContractForm(request.POST, show_project=False)
        if form.is_valid():
            with transaction.atomic():
                try:
                    contract = form.save(commit=False)
                    contract.project = project
                    contract.save()
                    form.save_m2m()
                except IntegrityError as e:
                    messages.add_message(request, messages.ERROR, e)
                    return redirect('project', pk=project.pk)

            messages.add_message(request, messages.SUCCESS, 'Contract created')
            return redirect('contract', pk=contract.id)
        return render(request, 'projects/create_contract.html', {
            'project': project,
            'form': form,
        })


@permission_required(Permissions.EDIT, 'project', (Project, 'pk', 'pk'))
def project_contract_remove(request, pk, cid):
    contract = get_object_or_404(Contract, pk=cid)
    contract.project = None
    contract.save()
    return HttpResponse("Contract removed from project")


class ProjectDelete(CheckerMixin, DeleteView):
    model = Project
    template_name = '../templates/generic_confirm_delete.html'
    success_url = reverse_lazy('projects')
    action_url = 'project_delete'
    success_message = "Project was deleted successfully."
    permission_required = Permissions.DELETE
    permission_target = 'project'

    def get_context_data(self, **kwargs):
        context = super(ProjectDelete, self).get_context_data(**kwargs)
        context['action_url'] = 'project_delete'
        context['id'] = self.object.id
        return context


def dsw_list_projects(request):
    #if data steward or admin -> list all the public projects
    # if(request.user.is_admin() | request.user.is_datasteward()):
    #     objects = Project.objects.all().filter(is_published=True)
    objects = (Project.objects.filter(local_custodians=request.user) | Project.objects.filter(company_personnel=request.user)).distinct()
    objects = objects.annotate(c=Count('datasets__exposures')).filter(c__gt=0)
    return render(request, 'integrations/dsw/project_list.html', {
        'dsw_origin': getattr(settings, 'DSW_ORIGIN', 'localhost'),
        'projects': [{'url': reverse('project', args=[str(project.id)]),
                      'acronym':project.acronym,
                      'title':project.title,
                      'id':project.id} for project in objects],
    })
