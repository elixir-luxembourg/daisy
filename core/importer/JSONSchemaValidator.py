import json
import jsonschema
import os
import urllib

from django.conf import settings

from core.exceptions import JSONSchemaValidationError
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)

JSONSCHEMA_BASE_LOCAL_PATH = getattr(settings, "IMPORT_JSON_SCHEMAS_DIR")
JSONSCHEMA_BASE_REMOTE_URL = getattr(settings, "IMPORT_JSON_SCHEMAS_URI")


class BaseJSONSchemaValidator:
    @property
    def schema_name(self):
        raise NotImplementedError

    @property
    def validator(self):
        return self._cached_validator

    def validate_items(self, item_list, logger=None):
        for item in item_list:
            try:
                self.validator.validate(item)
            except jsonschema.ValidationError as e:
                raise JSONSchemaValidationError(str(e))
        return True

    def __init__(self):
        self.base_url = JSONSCHEMA_BASE_REMOTE_URL
        self.base_path = JSONSCHEMA_BASE_LOCAL_PATH
        self._make_validator()

    def _make_validator(self):
        schema = self._load_schema(self.schema_name)

        def get_referenced_schema(uri):
            # TODO: at the moment, all schemas are under same URI directory
            # the following will probably fail in cases the subschema is in different path
            schema_name = os.path.basename(uri)
            referenced_schema = self._load_schema(schema_name)
            return referenced_schema

        resolver = jsonschema.RefResolver(
            self.base_path,
            schema,
            handlers={
                "https": get_referenced_schema,
                "http": get_referenced_schema,
            },
        )
        self._cached_validator = jsonschema.Draft4Validator(schema, resolver=resolver)
        return

    def _load_schema(self, schema_name):
        try:
            return self._load_schema_from_disk(schema_name)
        except Exception as e:
            import os

            logger.warning(
                "Error (1/2) loading schema from disk for JSON validation...: " + str(e)
            )
            logger.warning("Working directory = " + os.getcwd())
            logger.warning("File path = " + os.path.join(self.base_path, schema_name))
            logger.warning("Will try to load the schema from URL...")

        try:
            return self._load_schema_from_url(schema_name)
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logger.error(
                "Error (2/2) loading schema from URI for JSON validation...: " + str(e)
            )
            logger.error("URL = " + os.path.join(self.base_url, schema_name))

        raise Exception("Cannot load schema for JSON validation")

    def _load_schema_from_disk(self, schema_name):
        file_path = os.path.join(self.base_path, schema_name)
        with open(file_path, "r") as opened_file:
            return json.load(opened_file)

    def _load_schema_from_url(self, schema_name):
        file_path = os.path.join(self.base_url, schema_name)
        with urllib.request.urlopen(file_path) as url:
            return json.loads(url.read().decode())


class DatasetJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-dataset.json"


class ProjectJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-project.json"


class InstitutionJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-institution.json"


class SubmissionJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-study.json"
