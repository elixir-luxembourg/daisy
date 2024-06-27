from django.apps import AppConfig
from django.conf import settings
import os
import json
from django.core.exceptions import ImproperlyConfigured


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        import core.models.signals

        # Prevent use of conflicting versions of import JSON schemas
        json_schema_uri = getattr(settings, "IMPORT_JSON_SCHEMAS_URI")
        json_schema_dir = getattr(settings, "IMPORT_JSON_SCHEMAS_DIR")
        for file in os.listdir(json_schema_dir):
            with open(
                os.path.join(json_schema_dir, file), "r", encoding="utf-8"
            ) as schema_file:
                schema = json.loads(schema_file.read())
                local_schema_uri_basename = os.path.dirname(schema["$id"])
                settings_schema_uri_basename = os.path.dirname(json_schema_uri)
            if local_schema_uri_basename != settings_schema_uri_basename:
                raise ImproperlyConfigured(
                    "Version of import JSON schema is not matching version set in settings.py.\n"
                    f"{file} property $id: {local_schema_uri_basename}\n"
                    f"settings.py schema URI: {settings_schema_uri_basename}"
                )
