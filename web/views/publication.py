from django.contrib import messages
from django.contrib.messages import add_message
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, ListView, UpdateView

from core.forms import PublicationForm, PickPublicationForm
from core.models import Project
from core.models import Publication
from core.permissions import permission_required


class PublicationCreateView(CreateView):
    model = Publication
    template_name = 'publications/publication_form.html'
    form_class = PublicationForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('publications')

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class PublicationListView(ListView):
    model = Publication
    template_name = 'publications/publication_list.html'


class PublicationEditView(UpdateView):
    model = Publication
    template_name = 'publications/publication_form_edit.html'
    form_class = PublicationForm

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def get_success_url(self):
        return reverse_lazy('publication', kwargs={'pk': self.object.id})


@require_http_methods(["DELETE"])
@permission_required('EDIT', (Project, 'pk', 'pk'))
def remove_publication_from_project(request, pk, publication_id):
    project = get_object_or_404(Project, pk=pk)
    project.publications.remove(publication_id)
    return HttpResponse("Publication unlinked from project")


@permission_required('EDIT', (Project, 'pk', 'pk'))
def pick_publication_for_project(request, pk):
    if request.method == 'POST':
        form = PickPublicationForm(request.POST)
        if form.is_valid():
            project = get_object_or_404(Project, pk=pk)
            publication_id = form.cleaned_data['publication']
            publication = get_object_or_404(Publication, pk=publication_id)
            project.publications.add(publication)
        else:
            return HttpResponseBadRequest("wrong parameters")
        project.save()
        add_message(request, messages.SUCCESS, "Publication added")
        return redirect(to='project', pk=pk)

    else:
        form = PickPublicationForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


@permission_required('EDIT', (Project, 'pk', 'pk'))
def add_publication_to_project(request, pk):
    if request.method == 'POST':
        form = PublicationForm(request.POST)
        if form.is_valid():
            project = get_object_or_404(Project, pk=pk)
            publication = form.save()
            project.publications.add(publication)
            project.save()
            add_message(request, messages.SUCCESS, "Publication added")
        else:
            error_messages = []
            for field, error in form.errors.items():
                error_message = "{}: {}".format(field, error[0])
                error_messages.append(error_message)
            add_message(request, messages.ERROR, "\n".join(error_messages))
        return redirect(to='project', pk=pk)

    else:
        form = PublicationForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})
