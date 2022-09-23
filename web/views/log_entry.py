from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from core.models.user import User
from core.permissions import constants, CheckerMixin
from auditlog.models import LogEntry
from auditlog.registry import auditlog

from collections import defaultdict
import datetime
import json

class LogEntryListView(CheckerMixin, ListView):
    DATE_FORMAT = "%Y-%m-%d"
    model = LogEntry
    allow_empty = True
    permission_required = constants.Permissions.PROTECTED

    template_name = 'history/log_entry_list.html'

    # TODO
    #  - Make cleaner
    def get_list_of_model_fields(self):
        fields_per_model = LogEntry.objects.values("content_type", "changes").distinct().all()
        tmp_dict = defaultdict(lambda: {})
        for entry in fields_per_model:
            entry_content_type = ContentType.objects.get(pk=entry["content_type"])
            entry_model = entry_content_type.model_class()
            entry_model_name = entry_content_type.name
            changed_fields = json.loads(entry["changes"]).keys()

            for key in changed_fields:
                field_name = self.get_verbose_field_name(entry_model, key)
                tmp_dict[entry_model_name].update({key: field_name})

        model_fields_dict = {
            key: {name: verbose_name for name, verbose_name in sorted(values.items(), key=lambda x: x[1])}
            for key, values in tmp_dict.items()
        }
        return model_fields_dict

    def get_verbose_field_name(self, model, field_name):
        # Copy of method used by LogEntry.changes_display_dict
        model_fields = auditlog.get_model_fields(model._meta.model)
        field = model._meta.get_field(field_name)
        verbose_name = model_fields.get("mappings_fields", {}).get(
            field.name, getattr(field, "verbose_name", field.name)
        )
        return verbose_name.title()

    def get_context_data(self, object_list=None, filters=None, **kwargs):
        query_filters = {}
        hidden_filters = {}

        start_date = datetime.datetime.strptime(filters["start_date"], self.DATE_FORMAT) \
            if "start_date" in filters \
            else datetime.date.today() - datetime.timedelta(days=90)

        query_filters.update({"timestamp__date__gte": start_date})

        end_date = datetime.datetime.strptime(filters["end_date"], self.DATE_FORMAT) \
            if "end_date" in filters \
            else datetime.datetime.now()
        query_filters.update({"timestamp__date__lte": end_date})

        if "action" in filters:
            query_filters.update({"action__exact": filters["action"]})

        if "user" in filters:
            query_filters.update({"actor__exact": filters["user"]})

        if "entity_name" in filters:
            query_filters.update({"content_type__model": filters["entity_name"]})
            hidden_filters.update({"entity_name": filters["entity_name"]})
            if "entity_attr" in filters:
                field = filters["entity_attr"]
                query_filters.update({"changes__regex": rf'"{field}": \['})

            if "entity_id" in filters:
                entity_class = get_object_or_404(ContentType, model=filters["entity_name"]).model_class()
                entity_object = get_object_or_404(entity_class, pk=filters["entity_id"])
                self.object_list = [
                    {"action": log.Action.choices[log.action], "log": log}
                    for log in entity_object.history.filter(**query_filters).all()
                ]
                hidden_filters.update({"entity_id": filters["entity_id"]})
            else:
                if "parent_entity_name" in filters and "parent_entity_id" in filters:
                    entity_class = get_object_or_404(ContentType, model=filters["entity_name"]).model_class()
                    entity_ids_list = [
                        o.pk for o in entity_class.objects.filter(**{filters["parent_entity_name"]: filters["parent_entity_id"]})
                    ]
                    query_filters.update({"object_id__in": entity_ids_list})
                    hidden_filters.update({
                        "parent_entity_name": filters["parent_entity_name"],
                        "parent_entity_id": filters["parent_entity_id"],
                    })

        if not hasattr(self, "object_list"):
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
        context['hidden_filters'] = hidden_filters
        context["log_actions"] = LogEntry.Action.choices
        context["model_fields"] = self.get_list_of_model_fields()

        return context

    def check_permissions(self, request):
        if request.user.is_superuser or request.user.is_part_of(constants.Groups.DATA_STEWARD.value) or request.user.is_part_of(constants.Groups.AUDITOR.value):
            return None
        else:
            if "entity_name" in request.GET and "entity_id" in request.GET:
                self.referenced_class = get_object_or_404(ContentType, model=request.GET.get("entity_name")).model_class()
                self.object = get_object_or_404(self.referenced_class, pk=request.GET.get("entity_id"))
            elif "parent_entity_name" in request.GET and "parent_entity_id" in request.GET:
                self.referenced_class = get_object_or_404(ContentType, model=request.GET.get("parent_entity_name")).model_class()
                self.object = get_object_or_404(self.referenced_class, pk=request.GET.get("parent_entity_id"))
            else:
                raise PermissionDenied()
            super().check_permissions(request)

    def get(self, request, *args, **kwargs):
        self.check_permissions(request)
        context = self.get_context_data(filters=request.GET)
        return self.render_to_response(context)
