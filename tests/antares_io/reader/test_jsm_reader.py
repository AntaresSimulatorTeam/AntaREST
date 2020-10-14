import json
from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import JsmReader


@pytest.mark.unit_test
def test_jsm_reader(tmp_path: str) -> None:

    path_jsm = Path(tmp_path) / "jsonschema.json"

    content_jsm = """
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "address": {"$ref": "address.json#/definitions/address"}
        }
    }
    """

    path_jsm.write_text(content_jsm)

    path_adress_jsm = Path(tmp_path) / "address.json"

    content_adress_jsm = """
    {
        "type": "object",
        "definitions": {
            "address": {
                "type": "object",
                "properties": {
                    "city": {"$ref": "#/definitions/city"}
                }
            },
            "city": {
                "type": "string"
            }
        }
    }
    """

    path_adress_jsm.write_text(content_adress_jsm)

    expected_jsm = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "address": {
                "properties": {"city": {"type": "string"}},
                "type": "object",
            }
        },
    }

    path_jsm.write_text(content_jsm)
    jsm = JsmReader.read(path_jsm)

    assert jsm == expected_jsm
