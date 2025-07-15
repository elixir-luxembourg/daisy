from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, UpdateView
from django.urls import reverse_lazy

from core.constants import Permissions
from core.forms import DACForm, DACFormEdit, PickContactWithRemarkForm, PickDatasetForm
from core.models import DAC, DacMembership, Dataset, Contract, Contact
from core.models.utils import COMPANY
from core.permissions import CheckerMixin, permission_required
from core.utils import DaisyLogger
from web.views.utils import AjaxViewMixin, is_data_steward
from . import facet_view_utils

log = DaisyLogger(__name__)

FACET_FIELDS = settings.FACET_FIELDS["dac"]


class DACCreateView(CreateView):
    model = DAC
    template_name = "dac/dac_form.html"
    form_class = DACForm
    permission_required = Permissions.EDIT
    permission_target = "dac"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            return super().dispatch(request, *args, **kwargs)
        if not request.POST.get("contract"):
            messages.error(request, "Please select a contract to create a DAC.")
            return redirect("dac_add")

        self.contract = Contract.objects.get(id=request.POST.get("contract"))
        can_edit = request.user.can_edit_contract(self.contract)
        if can_edit:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.assign_permissions_to_dac(form.instance)
        messages.add_message(self.request, messages.SUCCESS, "DAC created successfully")
        return response


class DACEditView(UpdateView):
    model = DAC
    template_name = "dac/dac_form_edit.html"
    form_class = DACFormEdit
    permission_required = Permissions.EDIT
    permission_target = "dac"

    def dispatch(self, request, *args, **kwargs):
        dac = self.get_object()
        if self.request.user.can_edit_dac(dac):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def get_success_url(self):
        return reverse_lazy("dac", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.add_message(self.request, messages.SUCCESS, "DAC edited successfully")
        return response


class DACDetailView(DetailView):
    model = DAC
    template_name = "dac/dac.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["memberships"] = DacMembership.objects.filter(dac=context["dac"])
        context["local_custodians"] = context["dac"].local_custodians.all()
        context["datasets"] = context["dac"].datasets.all()
        context["can_edit"] = self.request.user.can_edit_dac(context["dac"])
        context["is_data_steward"] = self.request.user.is_data_steward
        return context


class DACCreateCardView(CheckerMixin, CreateView, AjaxViewMixin):
    model = DAC
    template_name = "dac/dac_form.html"
    form_class = DACForm
    permission_required = Permissions.EDIT
    permission_target = "contract"

    def check_permissions(self, request):
        self.contract_id = request.resolver_match.kwargs.get("contract_pk")
        if self.contract_id:
            self.permission_object = get_object_or_404(Contract, id=self.contract_id)
        super().check_permissions(request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # pass the contract_id to the form to prepopulate the contract field
        kwargs["contract_id"] = self.contract_id
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.assign_permissions_to_dac(form.instance)
        messages.add_message(self.request, messages.SUCCESS, "DAC created successfully")
        return response

    def get_success_url(self, **kwargs):
        return reverse_lazy("dataset", kwargs={"pk": self.permission_object.pk})


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
            "title": "Data Access Committees",
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
@permission_required(Permissions.EDIT, "dac", (DAC, "pk", "dac_pk"))
def remove_member_from_dac(request, dac_pk, member_pk):
    try:
        membership = DacMembership.objects.get(dac_id=dac_pk, pk=member_pk)
        membership.delete()
        return HttpResponse("Member removed from DAC")
    except DacMembership.DoesNotExist:
        return HttpResponse("Membership not found", status=404)


@permission_required(Permissions.EDIT, "dac", (DAC, "pk", "dac_pk"))
def pick_member_for_dac(request, dac_pk):
    if request.method == "POST":
        form = PickContactWithRemarkForm(request.POST)
        if form.is_valid():
            dac = get_object_or_404(DAC, pk=dac_pk)
            contact_id = form.cleaned_data["contact"]
            contact = get_object_or_404(Contact, pk=contact_id)
            dac.members.add(contact)
            membership = DacMembership.objects.get(dac_id=dac_pk, contact=contact)
            membership.remark = form.cleaned_data["remark"]
            membership.save()
            messages.add_message(request, messages.SUCCESS, "Member added")
        return redirect(to="dac", pk=dac_pk)
    else:
        form = PickContactWithRemarkForm(**{"dac": dac_pk})

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )


@user_passes_test(is_data_steward)
def pick_dataset_for_dac(request, dac_pk):
    if request.method == "POST":
        form = PickDatasetForm(request.POST)
        if form.is_valid():
            dac = get_object_or_404(DAC, pk=dac_pk)
            dataset_id = form.cleaned_data["dataset"]
            dataset = get_object_or_404(Dataset, pk=dataset_id)
            dataset.dac = dac
            dataset.save()
            messages.add_message(request, messages.SUCCESS, "Dataset added")
        return redirect(to="dac", pk=dac_pk)
    else:
        form = PickDatasetForm()

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )
