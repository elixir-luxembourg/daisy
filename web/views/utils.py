from django.http import JsonResponse
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import FormMixin


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


def get_client_ip(request):
    ip_from_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_from_forwarded_for:
        return ip_from_forwarded_for.split(',')[0]    
    return request.META.get('REMOTE_ADDR')
