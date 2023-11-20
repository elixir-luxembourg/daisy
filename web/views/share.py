from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django.shortcuts import get_object_or_404

from core.forms.share import ShareForm, shareFormFactory, ShareEditForm
from core.models import Share, Dataset, Partner
from core.constants import Permissions
from core.permissions import permission_required, CheckerMixin
from core.utils import DaisyLogger

from web.views.utils import AjaxViewMixin


log = DaisyLogger(__name__)


class ShareCreateView(CheckerMixin, CreateView, AjaxViewMixin):
    model = Share
    template_name = "shares/share_form.html"
    form_class = ShareForm
    permission_required = Permissions.EDIT
    permission_target = "dataset"

    def check_permissions(self, request):
        edited_dataset_pk = request.resolver_match.kwargs["dataset_pk"]
        self.permission_object = Dataset.objects.get(pk=edited_dataset_pk)
        super().check_permissions(request)
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
        if self.dataset:
            self.object.dataset = self.dataset

        self.object.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Data logbook entry created"
        )
        return super().form_valid(form)

    def get_form(self, form_class=None):
        partner = self.request.GET.get("partner", None)
        if partner is not None:
            partner = get_object_or_404(Partner, pk=int(partner))
        return shareFormFactory(
            partner=partner, dataset=self.dataset, **self.get_form_kwargs()
        )

    def get_success_url(self, **kwargs):
        if self.dataset:
            return reverse_lazy("dataset", kwargs={"pk": self.dataset.pk})
        return super().get_success_url()


class ShareEditView(CheckerMixin, UpdateView, AjaxViewMixin):
    model = Share
    template_name = "shares/share_form.html"
    form_class = ShareEditForm
    permission_required = Permissions.EDIT
    permission_target = "dataset"

    def get_permission_object(self):
        obj = super().get_permission_object()
        return obj.dataset

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Data logbook entry updated"
        )
        return super().form_valid(form)

    def get_form(self, form_class=None):
        partner = self.request.GET.get("partner", None)
        if partner is not None:
            partner = get_object_or_404(Partner, pk=int(partner))
        return shareFormFactory(
            partner=partner, dataset=self.object.dataset, **self.get_form_kwargs()
        )

    def get_success_url(self, **kwargs):
        if self.object.dataset:
            return reverse_lazy("dataset", kwargs={"pk": self.object.dataset.pk})
        return super().get_success_url()


@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, "dataset", (Dataset, "pk", "dataset_pk"))
def remove_share(request, dataset_pk, share_pk):
    share = get_object_or_404(Share, pk=share_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if share.dataset == dataset:
        share.delete()
    return HttpResponse("Share deleted")
