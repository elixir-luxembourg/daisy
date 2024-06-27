import os

import pytest

from core.models import Dataset, Project, DataDeclaration
from test import factories
from django.conf import settings
from json import loads
from importlib import import_module


@pytest.mark.parametrize(
    "validator_class",
    [
        "DatasetJSONSchemaValidator",
        "ProjectJSONSchemaValidator",
        "InstitutionJSONSchemaValidator",
    ],
)
def test_json_schema_version(
    celery_session_worker, can_defer_constraint_checks, validator_class
):
    validator_class = getattr(
        import_module("core.importer.JSONSchemaValidator"), validator_class
    )
    validator = validator_class()
    schema_filename = os.path.join(validator.base_path, validator.schema_name)
    with open(schema_filename) as f:
        schema = loads(f.read())
    assert os.path.dirname(schema.get("$id")) == os.path.dirname(
        settings.IMPORT_JSON_SCHEMAS_URI
    )


@pytest.mark.skip("TBD")
def test_json_schema_validation():
    # Test validators on demo data
    pass
