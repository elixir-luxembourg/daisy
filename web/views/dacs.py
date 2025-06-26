from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib import messages
from django.db import transaction

from core.forms import DACForm, DACFormEdit
from core.models import DAC, DacMembership, Dataset
from core.models.utils import COMPANY
from core.permissions import CheckerMixin
from core.utils import DaisyLogger
from core.constants import Permissions
from web.views.utils import AjaxViewMixin
from . import facet_view_utils


log = DaisyLogger(__name__)

FACET_FIELDS = settings.FACET_FIELDS["dac"]


class DACCreateView(CreateView):
    model = DAC
    template_name = "dac/dac_form.html"
    form_class = DACForm

    def get_initial(self):
        initial = super().get_initial()
        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial["dataset_id"] = dataset_id
        return initial


class DACDetailView(DetailView):
    model = DAC
    template_name = "dac/dac.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["memberships"] = DacMembership.objects.filter(dac=context["dac"])
        context["local_custodians"] = context["dac"].local_custodians.all()
        context["datasets"] = context["dac"].datasets.all()
        context["can_edit"] = self.request.user.has_perm(
            Permissions.EDIT, context["dac"]
        )
        return context


class DACEditView(UpdateView):
    model = DAC
    template_name = "dac/dac_form_edit.html"
    form_class = DACFormEdit

    def get_success_url(self):
        return reverse_lazy("dac", kwargs={"pk": self.object.id})


class DACCreateCardView(CheckerMixin, CreateView, AjaxViewMixin):
    model = DAC
    template_name = "dac/dac_form.html"
    form_class = DACForm
    permission_required = Permissions.EDIT
    permission_target = "dac"

    def check_permissions(self, request):
        dataset_id = request.resolver_match.kwargs["dataset_pk"]
        self.permission_object = get_object_or_404(Dataset, id=dataset_id)
        super().check_permissions(request)

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.save()
            messages.add_message(
                self.request, messages.SUCCESS, "DAC created successfully"
            )
            if self.permission_object and not self.permission_object.dac:
                self.permission_object.dac = self.object
                self.permission_object.save()
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    f"DAC {self.object.id} added to Dataset {self.permission_object.id} successfully",
                )
            form.members = form.cleaned_data.get("members", [])
            if form.members:
                for member in form.members:
                    self.object.members.add(member)
                    messages.add_message(
                        self.request,
                        messages.SUCCESS,
                        f"Member {member} added to DAC {self.object.id} successfully",
                    )
            else:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    "No members were added to the DAC. Please add members to the DAC.",
                )
            messages.add_message(
                self.request,
                messages.SUCCESS,
                f"DAC {self.object.id} created successfully",
            )
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy("dataset", kwargs={"pk": self.permission_object.pk})


class DACEditCardView(CheckerMixin, UpdateView, AjaxViewMixin):
    model = DAC
    form_class = DACFormEdit
    template_name = "dac/dac_form.html"
    permission_required = Permissions.EDIT
    permission_target = "dac"

    def get_permission_object(self, queryset=None):
        return self.get_object()

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""
        self.object = form.save(commit=False)
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "DAC updated successfully")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dac", kwargs={"pk": self.object.pk})


def dac_list(request):
    query = request.GET.get("query")
    order_by = request.GET.get("order_by")
    dacs = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist("filters"),
        query=query,
        object_model=DAC,
        facets=FACET_FIELDS,
        order_by=order_by,
    )
    return render(
        request,
        "search/search_page.html",
        {
            "reset": True,
            "filters": request.GET.get("filters") or "",
            "order_by": order_by or "",
            "facets": facet_view_utils.filter_empty_facets(dacs.facet_counts()),
            "query": query or "",
            "title": "DACs",
            "help_text": DAC.AppMeta.help_text,
            "search_url": "dacs",
            "add_url": "dac_add",
            "data": {"dacs": dacs},
            "results_template_name": "search/_items/dacs.html",
            "company_name": COMPANY,
            "order_by_fields": [
                ("Title", "title_l"),
            ],
        },
    )
