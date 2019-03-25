from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages import add_message
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, ListView, DetailView, UpdateView

from core.forms import RestrictionForm
from core.models import Restriction, Dataset
from core.permissions import permission_required


@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def remove_restriction_from_dataset(request, pk, restriction_id):
    restriction = get_object_or_404(Restriction, pk=restriction_id)
    dataset = get_object_or_404(Dataset, pk=pk)
    dataset.use_restrictions.remove(restriction)
    return HttpResponse("Storage location unlinked")


@permission_required('EDIT', (Dataset, 'pk', 'pk'))
def add_restriction_to_dataset(request, pk):
    if request.method == 'POST':
        form = RestrictionForm(request.POST)
        if form.is_valid():
            dataset = get_object_or_404(Dataset, pk=pk)
            restriction = form.save()
            dataset.use_restrictions.add(restriction)
            dataset.save()
            add_message(request, messages.SUCCESS, "Use restriction added")
        else:
            error_messages = []
            for field, error in form.errors.items():
                error_message = "{}: {}".format(field, error[0])
                error_messages.append(error_message)
            add_message(request, messages.ERROR, "\n".join(error_messages))
        return redirect(to='dataset', pk=pk)

    else:
        form = RestrictionForm()

    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


class RestrictionCreateView(CreateView):
    model = Restriction
    template_name = 'restrictions/restriction_form.html'
    form_class = RestrictionForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'user': self.request.user})
        return initial

    def get_success_url(self):
        return reverse_lazy('restrictions')


class RestrictionListView(ListView):
    model = Restriction
    template_name = 'restrictions/restrictions_list.html'


class RestrictionDetailView(DetailView):
    model = Restriction
    template_name = 'restrictions/restriction.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@method_decorator(staff_member_required, name='dispatch')
class RestrictionEditView(UpdateView):
    model = Restriction
    template_name = 'restrictions/restriction_form_edit.html'
    form_class = RestrictionForm

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def get_success_url(self):
        return reverse_lazy('restriction', kwargs={'pk': self.object.id})
