import json
import jsonschema
import sys
import urllib.request

from core.exceptions import JSONSchemaValidationError


JSONSCHEMA_BASE_LOCAL_PATH = './core/fixtures/'
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
            print("Error loading schema from disk for JSON validation...: " + str(e), file=sys.stderr) 
            print("Working directory = " + os.getcwd(), file=sys.stderr) 
            print("File path = " + self.base_path + self.schema_name, file=sys.stderr)
            print("\nWill try to load the schema from URL...", file=sys.stderr)

        try:
            self._cached_schema = self._load_schema_from_url()
            return
        except:
            print("Error loading schema from URI for JSON validation...: " + str(e), file=sys.stderr)
            print("URL = " + self.base_url + self.schema_name, file=sys.stderr) 

        raise Exception('Cannot load schema for JSON validation')

    def _load_schema_from_disk(self):
        with open(self.base_path + self.schema_name, 'r') as opened_file:
            return json.load(opened_file)

    def _load_schema_from_url(self):
        with urllib.request.urlopen(self.base_url + self.schema_name) as url:
            return json.loads(url.read().decode())

class DatasetJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-dataset.json"


class ProjectJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-project.json"


class InstitutionJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_name = "elu-institution.json"


class SubmissionJSONSchema(BaseJSONSchemaValidator):
    schema_name = "elu-study.json"
