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
            print(f"Getting logs before {date}")
            filters.update({"timestamp__lte": date})

        if "user" in request.GET.keys():
            filters.update({"actor__exact": request.GET.get("user")})

        self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in LogEntry.objects.filter(**filters)]
        context = self.get_context_data()
        return self.render_to_response(context)


        # if entity_name is not None and pk is not None:
        #
        # elif entity_name is not None:
        #     self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in get_list_or_404(LogEntry, content_type__model=entity_name)]
        #
        # else:
        #     self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in LogEntry.objects.all()]
        #

