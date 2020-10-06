# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

import pytest

project_dir: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api_iso_antares.types import JSON


@pytest.fixture
def test_jsonschema() -> JSON:
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
    jsonschema: JSON = json.loads(jsonschema_litteral)
    return jsonschema


@pytest.fixture
def test_json_data() -> JSON:
    json_data = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    return json_data
