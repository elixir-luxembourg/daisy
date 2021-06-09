from django.http import JsonResponse
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import FormMixin
from sequences import get_next_value


class AjaxViewMixin(SingleObjectTemplateResponseMixin, FormMixin):
    template_name_ajax = '_includes/forms.html'

    def get_template_names(self):
        if self.request.is_ajax():
            return [self.template_name_ajax]
        return super().get_template_names()

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
                'label': str(self.object)
            }
            return JsonResponse(data)
        return response


def generate_elu_accession(_=None):
    elu_accession = 'ELU_I_' + str(get_next_value('elu_accession', initial_value=100))
    return elu_accession
