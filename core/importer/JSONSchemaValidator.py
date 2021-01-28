import json
import jsonschema
import os
import sys
import urllib.request

from django.conf import settings

from core.exceptions import JSONSchemaValidationError
from core.utils import DaisyLogger


logger = DaisyLogger(__name__)

JSONSCHEMA_BASE_LOCAL_PATH = os.path.join(settings.BASE_DIR, 'core', 'fixtures')
JSONSCHEMA_BASE_REMOTE_URL = "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/"


class BaseJSONSchemaValidator:
    @property
    def schema_name(self):
        raise NotImplementedError

    @property
    def schema(self):
        return self._cached_schema

    def validate_items(self, item_list, logger=None):
        for item in item_list:
            try:
                jsonschema.validate(item, self.schema)
            except jsonschema.ValidationError as e:
                raise JSONSchemaValidationError(str(e))
        return True
    
    def __init__(self):
        self.base_url = JSONSCHEMA_BASE_REMOTE_URL
        self.base_path = JSONSCHEMA_BASE_LOCAL_PATH
        self._preload_schema()

    def _preload_schema(self):
        try:
            self._cached_schema = self._load_schema_from_disk()
            return 
        except Exception as e:
            import os
            logger.warn("Error (1/2) loading schema from disk for JSON validation...: " + str(e))
            logger.warn("Working directory = " + os.getcwd()) 
            logger.warn("File path = " + os.path.join(self.base_path, self.schema_name))
            logger.warn("Will try to load the schema from URL...")

        try:
            self._cached_schema = self._load_schema_from_url()
            return
        except:
            logger.error("Error (2/2) loading schema from URI for JSON validation...: " + str(e))
            logger.error("URL = " + os.path.join(self.base_url, self.schema_name))

        raise Exception('Cannot load schema for JSON validation')

    def _load_schema_from_disk(self):
        file_path = os.path.join(self.base_path, self.schema_name)
        with open(file_path, 'r') as opened_file:
            return json.load(opened_file)

    def _load_schema_from_url(self):
        file_path = os.path.join(self.base_url, self.schema_name)
        with urllib.request.urlopen(file_path) as url:
            return json.loads(url.read().decode())

class DatasetJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-dataset.json"


class ProjectJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-project.json"


class InstitutionJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-institution.json"


class SubmissionJSONSchema(BaseJSONSchemaValidator):
    schema_name = "elu-study.json"
