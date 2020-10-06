from pathlib import Path
from unittest.mock import Mock

import pytest
import json

from jsonschema import ValidationError  # type: ignore

from antares_io.ini import IniReader
from api_iso_antares.antares_io.data import validate, SimulationReader

jsonschema_litteral = """
{
  "$id": "http://json-schema.org/draft-07/schema#",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "A small exemple.",
  "type": "object",
  "properties": {
    "part1": {
      "type": "object",
      "required": [
        "key_int",
        "key_str"
      ],
      "properties": {
        "key_int": {
          "type": "integer",
          "description": "A description"
        },
        "key_str": {
          "type": "string",
          "description": "An other description"
        }
      }
    },
    "part2": {
      "type": "object",
      "properties": {
        "key_bool": {
          "type": "boolean",
          "description": "A description"
        },
        "key_bool2": {
          "type": "boolean"
        }
      }
    }
  }
}
"""


@pytest.mark.unit_test
def test_validate_json_ok() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_validate_json_wrong_key() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"WRONG_KEY": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    with pytest.raises(ValidationError):
        validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_validate_json_wrong_type() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"key_int": 1.9, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    with pytest.raises(ValidationError):
        validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_read_simulation() -> None:
    # Input
    path = Path('my-simulation')

    # Mock
    ini_reader = IniReader()
    ini_reader.read_ini = Mock(return_value={"section": {"parms": 123}})

    # Expected
    expected_data = {'settings': {'generaldata.ini': {"section": {"parms": 123}}}}

    # Test
    simulation_reader = SimulationReader(reader_ini=ini_reader)
    res = simulation_reader.read_simulation(path)

    # Verify
    assert res == expected_data
    ini_reader.read_ini.assert_called_once_with(path / 'settings/generaldata.ini')
