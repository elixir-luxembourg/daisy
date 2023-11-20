from django.core.exceptions import ValidationError
from pytest import raises

from core.models.utils import validate_json
from test.factories import ProjectFactory


def test_json_validator():
    with raises(ValidationError):
        validate_json('{"this is not a valid json; it lacks the value"}')

    validate_json('{"is_it_a_valid_json": "yes, it definitely is!"}')
    assert True


def test_json_vaildation():
    project = ProjectFactory.create(title="Test project", acronym="Teste projecte")
    project.save()

    with raises(ValidationError):
        project.scientific_metadata = '{"this is not a valid json; it lacks the value"}'
        project.save()

    project.scientific_metadata = '{"is_it_a_valid_json": "yes, it definitely is!"}'
    project.save()
    assert True
