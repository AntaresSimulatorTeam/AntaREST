from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import IniReader, FolderReaderEngine
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.custom_types import JSON


@pytest.mark.integration_test
def test_reader_folder(
    lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    study_reader = FolderReaderEngine(
        reader_ini=IniReader(),
        jsonschema=lite_jsonschema,
        root=lite_path,
        jsm_validator=JsmValidator(jsm=lite_jsonschema),
    )

    res = study_reader.read(lite_path)
    assert res == lite_jsondata
