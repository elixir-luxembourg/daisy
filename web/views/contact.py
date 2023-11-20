from django.conf import settings
from django.contrib import messages
from django.contrib.messages import add_message
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from core.forms import ContactForm, PickContactForm
from core.models import Contact, Project
from core.models.utils import COMPANY
from core.permissions import permission_required, CheckerMixin

from web.views.utils import AjaxViewMixin
from core.constants import Permissions
from . import facet_view_utils

FACET_FIELDS = settings.FACET_FIELDS["contact"]


@require_http_methods(["DELETE"])
@permission_required(Permissions.EDIT, "project", (Project, "pk", "pk"))
def remove_contact_from_project(request, pk, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id)
    project = get_object_or_404(Project, pk=pk)
    project.contacts.remove(contact)
    return HttpResponse("Contact deleted")


@permission_required(Permissions.EDIT, "project", (Project, "pk", "pk"))
def pick_contact_for_project(request, pk):
    if request.method == "POST":
        form = PickContactForm(request.POST)
        if form.is_valid():
            project = get_object_or_404(Project, pk=pk)
            contact_id = form.cleaned_data["contact"]
            contact = get_object_or_404(Contact, pk=contact_id)
            project.contacts.add(contact)
        else:
            return HttpResponseBadRequest("wrong parameters")
        project.save()
        add_message(request, messages.SUCCESS, "Contact added")
        return redirect(to="project", pk=pk)

    else:
        form = PickContactForm()

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )


@permission_required(Permissions.EDIT, "project", (Project, "pk", "pk"))
def add_contact_to_project(request, pk):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            project = get_object_or_404(Project, pk=pk)
            contact = form.save()
            project.contacts.add(contact)
            project.save()
            add_message(request, messages.SUCCESS, "Contact added")
        else:
            error_messages = []
            for field, error in form.errors.items():
                error_message = f"{field}: {error[0]}"
                error_messages.append(error_message)
            add_message(request, messages.ERROR, "\n".join(error_messages))
        return redirect(to="project", pk=pk)

    else:
        form = ContactForm()

    return render(
        request,
        "modal_form.html",
        {"form": form, "submit_url": request.get_full_path()},
    )


class ContactCreateView(CreateView, AjaxViewMixin):
    model = Contact
    template_name = "contacts/contact_form.html"
    form_class = ContactForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({"user": self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy("contacts")


# class ContactListView(ListView):
#     model = Contact
#     template_name = 'contacts/contact_list.html'


class ContactDetailView(DetailView):
    model = Contact
    template_name = "contacts/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContactEditView(UpdateView):
    model = Contact
    template_name = "contacts/contact_form_edit.html"
    form_class = ContactForm

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def get_success_url(self):
        return reverse_lazy("contact", kwargs={"pk": self.object.id})


def contact_search_view(request):
    query = request.GET.get("query")
    order_by = request.GET.get("order_by")
    contacts = facet_view_utils.search_objects(
        request,
        filters=request.GET.getlist("filters"),
        query=query,
        object_model=Contact,
        facets=FACET_FIELDS,
        order_by=order_by,
    )
    return render(
        request,
        "search/search_page.html",
        {
            "reset": True,
            "facets": facet_view_utils.filter_empty_facets(contacts.facet_counts()),
            "query": query or "",
            "title": "Contacts",
            "help_text": Contact.AppMeta.help_text,
            "search_url": "contacts",
            "add_url": "contact_add",
            "data": {"contacts": contacts},
            "results_template_name": "search/_items/contacts.html",
            "company_name": COMPANY,
            "order_by_fields": [
                ("First Name", "first_name"),
                ("Last Name", "last_name"),
            ],
        },
    )


class ContactDelete(CheckerMixin, DeleteView):
    model = Contact
    template_name = "../templates/generic_confirm_delete.html"
    success_url = reverse_lazy("contacts")
    success_message = "Contact was deleted successfully."
    permission_required = Permissions.DELETE
    permission_target = "contact"

    def get_context_data(self, **kwargs):
        context = super(ContactDelete, self).get_context_data(**kwargs)
        context["action_url"] = "contact_delete"
        context["id"] = self.object.id
        return context
