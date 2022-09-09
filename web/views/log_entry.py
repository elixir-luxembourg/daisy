from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from guardian.mixins import PermissionRequiredMixin
from auditlog.models import LogEntry
import datetime

class LogEntryListView(PermissionRequiredMixin, ListView):
    model = LogEntry
    paginate_by = 5
    allow_empty = True
    permission_required = "constants.Permissions.VIEW"

    template_name = 'history/log_entry_list.html'

    def get_context_data(self, start_date=None, end_date=None, object_list=None, **kwargs):
        if start_date is None:
            start_date = datetime.date.today() - datetime.timedelta(days=90)
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.date.today().strftime("%Y-%m-%d")

        models_list_fk = LogEntry.objects.values("content_type").distinct().all()
        models_list_names = [ct["model"] for ct in ContentType.objects.values("model").filter(pk__in=models_list_fk).all()]
        context = super().get_context_data(**kwargs)
        context["models_list"] = models_list_names
        context["start_date"] = start_date
        context["end_date"] = end_date

        # FIXME
        if "parent_entity_name" in kwargs.keys() and "parent_entity_id" in kwargs.keys():
            context["parent_entity_name"] = kwargs.get("parent_entity_name")
            context["parent_entity_id"] = kwargs.get("parent_entity_id")

        if "user" in kwargs.keys():
            context["user"] = kwargs.get("user")

        return context

    def get(self, request, *args, **kwargs):
        if "entity_name" in request.GET.keys() and "entity_id" in request.GET.keys():
            entity_class = get_object_or_404(ContentType, model=request.GET.get("entity_name")).model_class()
            entity_object = get_object_or_404(entity_class, pk=request.GET.get("entity_id"))
            self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in entity_object.history.all()]
            context = self.get_context_data()
            return self.render_to_response(context)

        filters = {}
        if "entity_name" in request.GET.keys():
            filters.update({"content_type__model": request.GET.get("entity_name")})
            if "parent_entity_name" in request.GET.keys() and "parent_entity_id" in request.GET.keys():
                entity_class = get_object_or_404(ContentType, model=request.GET.get("entity_name")).model_class()
                entity_ids_list = [
                    o.pk for o in entity_class.objects.filter(**{request.GET.get("parent_entity_name"): request.GET.get("parent_entity_id")})
                ]
                filters.update({"object_id__in": entity_ids_list})

        if "start_date" in request.GET.keys():
            date = datetime.datetime.strptime(request.GET.get("start_date"), "%Y-%m-%d")
            filters.update({"timestamp__gte": date})

        if "end_date" in request.GET.keys():
            date = datetime.datetime.strptime(request.GET.get("end_date"), "%Y-%m-%d") + datetime.timedelta(days=1)
            filters.update({"timestamp__lte": date})

        if "user" in request.GET.keys():
            filters.update({"actor__exact": request.GET.get("user")})

        self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in LogEntry.objects.filter(**filters)]
        context = self.get_context_data(
            start_date=request.GET.get("start_date", None),
            end_date=request.GET.get("end_date", None),
            **filters,
        )

        return self.render_to_response(context)


