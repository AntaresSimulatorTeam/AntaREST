import json
from pathlib import Path

import pytest

from api_iso_antares.antares_io.validator import SwaggerValidator
from api_iso_antares.engine.swagger.engine import SwaggerEngine


@pytest.mark.unit_test
def test_json_to_yaml(path_resources: Path) -> None:

    path_data = path_resources / "swagger/example.json"
    json_data = json.load(path_data.open())
    yaml_data = SwaggerEngine.json_to_yaml(json_data)
    json_data_from_yaml = SwaggerEngine.yaml_to_json(yaml_data)

    assert json_data == json_data_from_yaml
    SwaggerValidator.validate(json_data_from_yaml)


@pytest.mark.unit_test
def test_parse(path_resources: Path) -> None:
    pass
