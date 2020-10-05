import configparser
import json

from api_iso_antares.antares_io.data import to_json_with_jsonschema


def test_to_json_with_jsonschema() -> None:
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

    jsonschema = json.loads(jsonschema_litteral)

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    config = configparser.ConfigParser()
    config.read_dict(expected_json)

    result_json = to_json_with_jsonschema(config, jsonschema)
    assert expected_json == result_json
