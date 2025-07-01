from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from core.forms import DACForm, DACFormEdit, PickContactForm, PickDatasetForm
from core.models import DAC, DacMembership, Dataset, Contract, Contact
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
        self.contract_id = request.resolver_match.kwargs.get("contract_pk")
        if self.contract_id:
            self.permission_object = get_object_or_404(Contract, id=self.contract_id)
        super().check_permissions(request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract_id"] = self.contract_id
        return kwargs

    def form_valid(self, form):
        """If the form is valid, save the associated model and add to the dataset"""

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.save()
            if self.permission_object and not self.permission_object.dac:
                self.permission_object.dac = self.object
                self.permission_object.save()
        messages.add_message(self.request, messages.SUCCESS, "DAC created successfully")
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


@require_http_methods(["DELETE"])
# @csrf_exempt
# @permission_required(Permissions.EDIT, "dac", (DAC, "pk", "pk"))
def remove_member_from_dac(request, dac_pk, member_pk):
    try:
        membership = DacMembership.objects.get(dac_id=dac_pk, pk=member_pk)
        membership.delete()
        return HttpResponse("Member removed from DAC")
    except DacMembership.DoesNotExist:
        return HttpResponse("Membership not found", status=404)


# @permission_required(Permissions.EDIT, "dac", (DAC, "pk", "pk"))
def pick_member_for_dac(request, dac_pk):
    if request.method == "POST":
        form = PickContactForm(request.POST)
        if form.is_valid():
            dac = get_object_or_404(DAC, pk=dac_pk)
            contact_id = form.cleaned_data["contact"]
            contact = get_object_or_404(Contact, pk=contact_id)
            dac.members.add(contact)
        else:
            return HttpResponseBadRequest("wrong parameters")
        messages.add_message(request, messages.SUCCESS, "Member added")
        return redirect(to="dac", pk=dac_pk)

    else:
        form = PickContactForm()

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )


# @permission_required(Permissions.EDIT, "dac", (DAC, "pk", "pk"))
def pick_dataset_for_dac(request, dac_pk):
    if request.method == "POST":
        form = PickDatasetForm(request.POST)
        if form.is_valid():
            dac = get_object_or_404(DAC, pk=dac_pk)
            dataset_id = form.cleaned_data["dataset"]
            dataset = get_object_or_404(Dataset, pk=dataset_id)
            dataset.dac = dac
            dataset.save()
        else:
            return HttpResponseBadRequest("wrong parameters")
        messages.add_message(request, messages.SUCCESS, "Dataset added")
        return redirect(to="dac", pk=dac_pk)

    else:
        form = PickDatasetForm()

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )
