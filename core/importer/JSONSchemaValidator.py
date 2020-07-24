import urllib.request
import json
import jsonschema
from core.exceptions import JSONSchemaValidationError


JSONSCHEMA_BASE_URL = "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/"


class BaseJSONSchemaValidator:

    @property
    def schema_url(self):
        raise NotImplementedError

    @property
    def schema(self):
        with urllib.request.urlopen(self.schema_url) as url:
            return json.loads(url.read().decode())

    def validate_items(self, item_list, logger=None):
        for item in item_list:
            try:
                jsonschema.validate(item, self.schema)
            except jsonschema.ValidationError:
                raise JSONSchemaValidationError(item)
        return True


class DatasetJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_url = JSONSCHEMA_BASE_URL + "elu-dataset.json"


class ProjectJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_url = JSONSCHEMA_BASE_URL + "elu-project.json"


class InstitutionJSONSchemaValidator(BaseJSONSchemaValidator):
    schema_url = JSONSCHEMA_BASE_URL + "elu-institution.json"


class SubmissionJSONSchema(BaseJSONSchemaValidator):
    schema_url = JSONSCHEMA_BASE_URL + "elu-study.json"
