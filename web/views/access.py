from core.forms.access import AccessForm, AccessEditForm
from web.views.utils import AjaxViewMixin
from django.views.generic import CreateView
from core.models import Access, Dataset
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from core.permissions import permission_required
from core.utils import DaisyLogger
from django.views.decorators.http import require_http_methods

log = DaisyLogger(__name__)

class AccessCreateView(CreateView, AjaxViewMixin):
    model = Access
    template_name = 'accesses/access_form.html'
    form_class = AccessForm

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
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, "Access created")
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


@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def edit_access(request, pk, dataset_pk):
    access = get_object_or_404(Access, pk=pk)
    if request.method == 'POST':
        form = AccessEditForm(request.POST,  request.FILES, instance=access)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Access definition updated")
            redirecturl = reverse_lazy('dataset', kwargs={'pk': dataset_pk})
            return redirect(to=redirecturl, pk=access.id)
        else:
            return JsonResponse(
                {'error':
                     {'type': 'Edit error', 'messages': [str(e) for e in form.errors]
                      }}, status=405)
    else:
        form = AccessEditForm(instance=access)

    log.debug(submit_url=request.get_full_path())
    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path() })

@require_http_methods(["DELETE"])
@permission_required('EDIT', (Dataset, 'pk', 'dataset_pk'))
def remove_access(request, dataset_pk, access_pk):
    access = get_object_or_404(Access, pk=access_pk)
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if access.dataset == dataset:
        access.delete()
    return HttpResponse("Access unlinked")