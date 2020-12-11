import json
from pathlib import Path

import jsonschema
import pytest

from api_iso_antares.antares_io.validator import SwaggerValidator


@pytest.mark.unit_test
def test_validates_documentation() -> None:
    with pytest.raises(jsonschema.exceptions.ValidationError):
        SwaggerValidator.validate({})


@pytest.mark.unit_test
def test_validates_example_swagger(path_ressources: Path) -> None:
    path_example = path_ressources / "swagger/example.json"
    json_data = json.loads(path_example.read_text())
    SwaggerValidator.validate(json_data)


@pytest.mark.unit_test
def test_get_jsonschema_swagger() -> None:
    jsm = SwaggerValidator._get_jsonschema_swagger()

    assert jsm["id"] == "https://spec.openapis.org/oas/3.0/schema/2019-04-02"
    assert jsm["patternProperties"] == {"^x-": {}}
    assert jsm["properties"]["servers"] == {
        "type": "array",
        "items": {"$ref": "#/definitions/Server"},
    }
