from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.jsonschema import JsonSchema
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.filesystem_engine import FileSystemEngine


@pytest.mark.integration_test
def test_reader_folder(
    lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    jsm = JsonSchema(lite_jsonschema)
    readers = {"default": IniReader()}

    study_reader = FileSystemEngine(jsm=jsm, readers=readers)
    res = study_reader.parse(lite_path)

    jsm_validator = JsmValidator(jsm=jsm)
    jsm_validator.validate(res)

    assert res == lite_jsondata
