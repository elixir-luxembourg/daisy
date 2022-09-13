from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from core.models.user import User
from core.models.dataset import Dataset
from core.permissions import constants, CheckerMixin
from auditlog.models import LogEntry
import datetime


class LogEntryListView(CheckerMixin, ListView):
    DATE_FORMAT = "%Y-%m-%d"
    model = LogEntry
    paginate_by = 5
    allow_empty = True
    permission_required = constants.Permissions.EDIT

    template_name = 'history/log_entry_list.html'

    def get_context_data(self, object_list=None, filters=None, **kwargs):
        query_filters = {}
        start_date = datetime.datetime.strptime(filters.get("start_date"), self.DATE_FORMAT) \
            if "start_date" in filters.keys() \
            else datetime.date.today() - datetime.timedelta(days=90)
        query_filters.update({"timestamp__date__gte": start_date})

        end_date = datetime.datetime.strptime(filters.get("end_date"), self.DATE_FORMAT) \
            if "end_date" in filters.keys() \
            else datetime.datetime.now()
        query_filters.update({"timestamp__date__lte": end_date})

        if "entity_name" in filters.keys() and "entity_id" in filters.keys():
            entity_class = get_object_or_404(ContentType, model=filters.get("entity_name")).model_class()
            entity_object = get_object_or_404(entity_class, pk=filters.get("entity_id"))
            self.object_list = [
                {"action": log.Action.choices[log.action], "log": log}
                for log in entity_object.history.filter(**query_filters).all()
            ]

        else:
            if "entity_name" in filters.keys():
                query_filters.update({"content_type__model": filters.get("entity_name")})
                if "parent_entity_name" in filters.keys() and "parent_entity_id" in filters.keys():
                    entity_class = get_object_or_404(ContentType, model=filters.get("entity_name")).model_class()
                    entity_ids_list = [
                        o.pk for o in entity_class.objects.filter(**{filters.get("parent_entity_name"): filters.get("parent_entity_id")})
                    ]
                    query_filters.update({"object_id__in": entity_ids_list})

            if "user_name" in filters.keys():
                query_filters.update({"actor__exact": filters.get("user_name")})

            self.object_list = [{"action": log.Action.choices[log.action], "log": log} for log in LogEntry.objects.filter(**query_filters).all()]

        context = super().get_context_data(**kwargs)

        models_list_fk = LogEntry.objects.values("content_type").distinct().all()
        models_list_names = [ct["model"] for ct in ContentType.objects.values("model").filter(pk__in=models_list_fk).all()]
        users_list_fk = LogEntry.objects.values("actor").distinct().all()
        users_list_names = User.objects.values("pk", "full_name").filter(pk__in=users_list_fk).all()
        context["models_list"] = models_list_names
        context["users_list"] = users_list_names
        context["start_date"] = start_date.strftime(self.DATE_FORMAT)
        context["end_date"] = end_date.strftime(self.DATE_FORMAT)
        return context

    def check_permissions(self, request):
        if request.user.is_superuser or request.user.is_part_of(constants.Groups.DATA_STEWARD.value) or request.user.is_part_of(constants.Groups.AUDITOR.value):
            return None
        else:
            if "entity_name" in request.GET.keys() and "entity_id" in request.GET.keys():
                self.referenced_class = get_object_or_404(ContentType, model=request.GET.get("entity_name")).model_class()
                self.object = get_object_or_404(self.referenced_class, pk=request.GET.get("entity_id"))
            elif "parent_entity_name" in request.GET.keys() and "parent_entity_id" in request.GET.keys():
                self.referenced_class = get_object_or_404(ContentType, model=request.GET.get("parent_entity_name")).model_class()
                self.object = get_object_or_404(self.referenced_class, pk=request.GET.get("parent_entity_id"))
            else:
                raise PermissionDenied()
            super().check_permissions(request)

    def get(self, request, *args, **kwargs):
        self.check_permissions(request)
        context = self.get_context_data(filters=request.GET)
        return self.render_to_response(context)
