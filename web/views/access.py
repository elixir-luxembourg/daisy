from django.views.generic import CreateView, UpdateView
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from core.forms.access import AccessForm, AccessEditForm
from core.models import Access, Dataset
from core.constants import Permissions, Groups
from core.permissions import CheckerMixin
from core.permissions import permission_required
from core.utils import DaisyLogger

from web.views.utils import AjaxViewMixin


log = DaisyLogger(__name__)


class AccessCreateView(CreateView, AjaxViewMixin):
    model = Access
    template_name = 'accesses/access_form.html'
    form_class = AccessForm

    def has_permissions(self, user, dataset):
        print(f"Is user a data steward: {user.is_part_of([Groups.DATA_STEWARD.name])}")
        print(f"User is custodian: {dataset.local_custodians.filter(pk=user.pk).exists()}")
        if user.is_part_of([Groups.DATA_STEWARD.name]):
            return True
        else:
            return dataset.local_custodians.filter(pk=user.pk).exists()

    def get(self, request, *args, **kwargs):
        dataset = get_object_or_404(Dataset, pk=kwargs['dataset_pk'])
        if self.has_permissions(request.user, dataset):
            return super().get(request, args, kwargs)
        else:
            raise PermissionDenied()

    def post(self, request, *args, **kwargs):
        dataset = get_object_or_404(Dataset, pk=kwargs['dataset_pk'])
        if self.has_permissions(request.user, dataset):
            return super().post(request, args, kwargs)
        else:
            raise PermissionDenied()

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
        if not self.request.user.is_anonymous:
            self.object.created_by = self.request.user
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, 'Access created')
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


class AccessEditView(CheckerMixin, UpdateView, AjaxViewMixin):
    model = Access
    template_name = 'accesses/access_form.html'
    form_class = AccessEditForm
    permission_required = Permissions.EDIT

    def form_valid(self, form):
        """If the form is valid, check that remark is updated then save the associated model and add to the dataset"""
        if "access_notes" not in form.changed_data:
            form.add_error("access_notes", "Changes must be justified. Please update this field")
            return super().form_invalid(form)

        self.object = form.save(commit=False)
        if not self.request.user.is_anonymous:
            self.object.created_by = self.request.user
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, 'Access updated')
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        if self.object.dataset:
            return reverse_lazy('dataset', kwargs={'pk': self.object.dataset.pk})
        return super().get_success_url()


@require_http_methods(['DELETE'])
@permission_required(Permissions.EDIT, (Dataset, 'pk', 'dataset_pk'))
def remove_access(request, dataset_pk, access_pk):
    access = get_object_or_404(Access, pk=access_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if access.dataset == dataset:
        access.delete()
    return HttpResponse('Access unlinked')
