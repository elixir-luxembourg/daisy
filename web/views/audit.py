from django.apps import apps
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import DetailView

from reversion_compare.views import HistoryCompareDetailView
from reversion.models import Version


@method_decorator(staff_member_required, name='dispatch')
class AuditDetailView(HistoryCompareDetailView):
    template_name = 'audit/detail.html'

    def get_queryset(self):
        model_name = self.kwargs['model_name']
        Model = apps.get_model('core', model_name)
        return Model.objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.kwargs['model_name']
        context['versions'] = Version.objects.get_for_object(self.object)
        for version in context['versions']:
            print(f'Version: {version}')
            print(f'Revision: {version.revision}')
        return context
