from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from core.models.user import User
from guardian.mixins import PermissionRequiredMixin
from auditlog.models import LogEntry
import datetime


class LogEntryListView(PermissionRequiredMixin, ListView):
    DATE_FORMAT = "%Y-%m-%d"
    model = LogEntry
    paginate_by = 5
    allow_empty = True
    permission_required = "constants.Permissions.VIEW"

    template_name = 'history/log_entry_list.html'

    def get_context_data(self, object_list=None, filters=None, **kwargs):
        if "entity_name" in filters.keys() and "entity_id" in filters.keys():
            entity_class = get_object_or_404(ContentType, model=filters.get("entity_name")).model_class()
            entity_object = get_object_or_404(entity_class, pk=filters.get("entity_id"))
            self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in entity_object.history.all()]

        query_filters = {}
        if "entity_name" in filters.keys():
            query_filters.update({"content_type__model": filters.get("entity_name")})
            if "parent_entity_name" in filters.keys() and "parent_entity_id" in filters.keys():
                entity_class = get_object_or_404(ContentType, model=filters.get("entity_name")).model_class()
                entity_ids_list = [
                    o.pk for o in entity_class.objects.filter(**{filters.get("parent_entity_name"): filters.get("parent_entity_id")})
                ]
                filters.update({"object_id__in": entity_ids_list})

        if "user" in filters.keys():
            filters.update({"actor__exact": filters.get("user")})

        start_date = datetime.datetime.strptime(filters.get("start_date"), self.DATE_FORMAT) \
            if "start_date" in filters.keys() \
            else datetime.date.today() - datetime.timedelta(days=90)
        query_filters.update({"timestamp__gte": start_date})

        end_date = datetime.datetime.strptime(filters.get("end_date"), self.DATE_FORMAT) \
            if "end_date" in filters.keys() \
            else datetime.date.today()
        query_filters.update({"timestamp__lte": end_date})

        self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in LogEntry.objects.filter(**query_filters)]
        context = super().get_context_data(**kwargs)

        models_list_fk = LogEntry.objects.values("content_type").distinct().all()
        models_list_names = [ct["model"] for ct in ContentType.objects.values("model").filter(pk__in=models_list_fk).all()]
        users_list_fk = LogEntry.objects.values("actor").distinct().all()
        users_list_names = User.objects.values("pk", "full_name").filter(pk__in=users_list_fk).all()
        print(users_list_fk)
        print(users_list_names)
        context["models_list"] = models_list_names
        context["users_list"] = users_list_names
        context["start_date"] = start_date.strftime(self.DATE_FORMAT)
        context["end_date"] = end_date.strftime(self.DATE_FORMAT)
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(filters=request.GET)
        return self.render_to_response(context)
