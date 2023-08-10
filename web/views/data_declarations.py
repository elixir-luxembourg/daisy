import json
import operator

from functools import reduce

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy

from haystack.query import SearchQuerySet

from core.constants import Permissions
from core.forms import (
    DataDeclarationForm,
    DataDeclarationSubFormOther,
    DataDeclarationSubFormNew,
)
from core.forms import DataDeclarationSubFormFromExisting, DataDeclarationEditForm
from core.forms.data_declaration import RestrictionFormset
from core.models import Dataset, Partner, DataDeclaration, UseRestriction
from core.permissions import permission_required, CheckerMixin
from core.utils import DaisyLogger


log = DaisyLogger(__name__)

DATA_DECLARATIONS_SUB_FORMS = [
    (DataDeclarationSubFormFromExisting, "data_declaration_sub_form_existing.html"),
    (DataDeclarationSubFormNew, "data_declaration_sub_form_new.html"),
    (DataDeclarationSubFormOther, "data_declaration_sub_form_other.html"),
]


def data_declarations_add_sub_form(request):
    declaration_type = request.GET.get("declaration_type")
    dataset_id = request.GET.get("dataset_id")
    if declaration_type is None or dataset_id is None:
        return HttpResponseBadRequest("invalid declaration_type or dataset_id argument")

    dataset_id = int(dataset_id)
    declaration_type = int(declaration_type)

    dataset = get_object_or_404(Dataset, id=dataset_id)
    form_class, template = DATA_DECLARATIONS_SUB_FORMS[declaration_type]
    form = form_class(dataset=dataset)
    context_form = form.get_context()
    context_form.update({"form": form, "dataset": dataset})
    return render(request, "data_declarations/" + template, context=context_form)


@permission_required(Permissions.EDIT, "dataset", (Dataset, "pk", "pk"))
def data_declarations_add(request, pk):
    template_name = "data_declarations/data_declaration_form.html"
    form_class = DataDeclarationForm
    dataset = get_object_or_404(Dataset, id=pk)
    if request.method == "GET":
        form = form_class(dataset=dataset)
        return render(
            request,
            template_name,
            {
                "dataset": dataset,
                "form": form,
                "submit_url": request.get_full_path(),
            },
        )
    if request.method == "POST":
        form = DataDeclarationForm(request.POST, dataset=dataset)
        if form.is_valid():
            data_declaration = DataDeclaration()
            data_declaration.dataset = dataset
            data_declaration.title = form.cleaned_data["title"]
            data_declaration_type = form.cleaned_data["type"]
            sub_form_class = DATA_DECLARATIONS_SUB_FORMS[int(data_declaration_type)][0]
            sub_form = sub_form_class(request.POST, dataset=dataset)
            if sub_form.is_valid():
                sub_form.update(data_declaration)
                data_declaration.save()
                sub_form.after_save(data_declaration)
                return redirect("dataset", pk=dataset.pk)
        return render(
            request,
            template_name,
            {
                "dataset": dataset,
                "form": form,
                "submit_url": request.get_full_path(),
            },
        )


def data_declarations_get_contracts(request):
    partner_id = request.GET.get("partner_id")
    dataset_id = request.GET.get("dataset_id")
    if partner_id is None or dataset_id is None:
        return HttpResponseBadRequest("invalid partner_id and/or dataset_id arguments")

    partner_id = int(partner_id)
    dataset_id = int(dataset_id)
    partner = get_object_or_404(Partner, id=partner_id)
    dataset = get_object_or_404(Dataset, id=dataset_id)
    form = DataDeclarationSubFormNew(partner=partner, dataset=dataset)
    context_form = form.get_context()
    context_form.update({"form": form})
    return render(
        request,
        "data_declarations/data_declaration_sub_form_new_contract.html",
        context=context_form,
    )


# Methods data_declarations_autocomplete  and data_dec_paginated_search
# should ideally be


def data_declarations_autocomplete(request):
    def list_or_none(attribute, result):
        value = getattr(result, attribute)
        if value:
            return list(value)
        return None

    query = request.GET.get("q")

    suggestions = []
    if query:
        sqs = SearchQuerySet().models(DataDeclaration).autocomplete(autocomplete=query)
        for result in sqs:
            cohorts = list_or_none("cohorts", result)
            local_custodians = list_or_none("local_custodians", result)
            data_types = list_or_none("data_types", result)
            suggestion = {
                "id": result.pk,
                "title": result.title,
                "project": result.project,
                "cohorts": cohorts,
                "local_custodians": local_custodians,
                "data_types": data_types,
                "text": result.title + ", Project: " + result.project,
            }
            suggestions.append(suggestion)
    the_data = json.dumps({"results": suggestions})
    return HttpResponse(the_data, content_type="application/json")


def data_dec_paginated_search(request):
    search = request.GET.get("search")
    page = request.GET.get("page")

    if search is None:
        return HttpResponseBadRequest("invalid search parameter")

    matching_declarations = DataDeclaration.objects.filter(
        Q(title__icontains=search)
        | Q(dataset__title__icontains=search)
        | Q(dataset__project__title__icontains=search)
    ).order_by("id")

    paginator = Paginator(matching_declarations, 25)

    if int(page) > paginator.num_pages:
        return HttpResponseBadRequest("invalid page parameter")

    matching_decs_on_page = paginator.get_page(page)

    results = []
    for matching_dec in matching_decs_on_page:
        results.append({"id": matching_dec.id, "text": matching_dec.get_long_name()})

    return JsonResponse(
        {"results": results, "pagination": {"more": int(page) < paginator.num_pages}}
    )


@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, "dataset", (DataDeclaration, "pk", "pk"))
def data_declarations_delete(request, pk):
    data_declaration = get_object_or_404(DataDeclaration, id=pk)
    data_declaration.delete()
    return HttpResponse("Data declaration deleted")


@permission_required(Permissions.EDIT, "dataset", (DataDeclaration, "pk", "pk"))
def data_declarations_duplicate(request, pk):
    data_declaration = get_object_or_404(DataDeclaration, id=pk)
    new_data_declaration = DataDeclaration()
    excluded_fields = [
        "pk",
        "id",
        "added",
        "updated",
        "unique_id",
        "other_external_id",
        "submission_id",
    ]
    new_data_declaration.copy(
        data_declaration, excluded_fields, ignore_many_to_many=True
    )
    new_data_declaration.title += "_clone"
    new_data_declaration.save()
    new_data_declaration.copy(
        data_declaration, excluded_fields, ignore_many_to_many=False
    )
    return redirect("dataset", pk=data_declaration.dataset.pk)


class DatadeclarationDetailView(DetailView):
    model = DataDeclaration
    template_name = "data_declarations/data_declaration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admin"] = self.request.user.is_admin_of_dataset(self.object.dataset)
        context["can_edit"] = self.request.user.can_edit_dataset(self.object.dataset)
        return context


class DatadeclarationEditView(CheckerMixin, UpdateView):
    model = DataDeclaration
    template_name = "data_declarations/data_declaration_form_edit.html"
    permission_required = Permissions.EDIT
    permission_target = "dataset"

    def get(self, request, *args, **kwargs):
        data_declaration = self.get_object()

        declaration_form = DataDeclarationEditForm(instance=data_declaration)
        restriction_data = [
            restriction.serialize()
            for restriction in data_declaration.data_use_restrictions.all()
        ]
        restriction_formset = RestrictionFormset(initial=restriction_data)
        return render(
            request,
            self.template_name,
            {
                "form": declaration_form,
                "submit_url": request.get_full_path(),
                "data_declaration": data_declaration,
                "restriction_formset": restriction_formset,
            },
        )

    def post(self, request, **kwargs):
        data_declaration = self.get_object()
        declaration_form = DataDeclarationEditForm(
            request.POST, instance=data_declaration
        )

        restriction_data = [
            restriction.serialize()
            for restriction in data_declaration.data_use_restrictions.all()
        ]
        restriction_formset = RestrictionFormset(request.POST, initial=restriction_data)

        formset_valid = restriction_formset.is_valid()

        if declaration_form.is_valid() and formset_valid:
            try:
                with transaction.atomic():
                    declaration_form.save()
                    # Replace the old use restrictions with the new
                    UseRestriction.objects.filter(
                        data_declaration=data_declaration
                    ).delete()
                    for restriction_form in restriction_formset:
                        if (
                            restriction_form.is_valid()
                            and not restriction_form.is_empty()
                        ):
                            restriction = restriction_form.save(commit=False)
                            restriction.data_declaration = data_declaration
                            restriction.save()
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        f"data declaration {data_declaration.title} edited",
                    )
            except IntegrityError:
                # If the transaction failed
                messages.add_message(
                    request,
                    messages.ERROR,
                    "An error occurred when saving data declaration",
                )
            return redirect("dataset", pk=data_declaration.dataset.id)
        else:
            return render(
                request,
                self.template_name,
                {
                    "form": declaration_form,
                    "submit_url": request.get_full_path(),
                    "data_declaration": data_declaration,
                    "restriction_formset": restriction_formset,
                },
            )
