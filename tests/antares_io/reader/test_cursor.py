import pytest

from api_iso_antares.antares_io.reader.cursor import JsmCursor


@pytest.mark.unit_test
def eetest_read_refs() -> None:
    little_schema_with_refs = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {
            "address": {
                "type": "object",
                "properties": {
                    "street_address": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                },
                "required": ["street_address", "city", "state"],
            }
        },
        "type": "object",
        "properties": {
            "billing_address": {"$ref": "#/definitions/address"},
            "shipping_address": {"$ref": "#/definitions/address"},
        },
    }

    cursor = JsmCursor(little_schema_with_refs)

    assert cursor.next("billing_address").next("city").jsm == {
        "type": "string"
    }
