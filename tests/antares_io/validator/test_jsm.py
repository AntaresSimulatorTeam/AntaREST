from pathlib import Path

import pytest
from jsonschema import ValidationError

from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_types import JSON
from api_iso_antares.jsm import JsonSchema


@pytest.mark.unit_test
def test_validation(
    lite_jsondata: JSON, lite_jsonschema: JSON, lite_path: Path
):
    del lite_jsondata["folder3"]["file3.ini"]

    jsm_validator = JsmValidator(JsonSchema(lite_jsonschema))

    with pytest.raises(ValidationError):
        jsm_validator.validate(lite_jsondata)


@pytest.mark.unit_test
def test_validation_sub_jsm(
    lite_jsondata: JSON, lite_jsonschema: JSON, lite_path: Path
):
    lite_jsondata = lite_jsondata["folder3"]

    jsm = JsonSchema(lite_jsonschema).get_child("folder3")
    jsm_validator = JsmValidator(jsm)

    jsm_validator.validate(lite_jsondata)
