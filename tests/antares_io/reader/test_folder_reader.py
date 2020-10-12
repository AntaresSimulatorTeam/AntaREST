from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.antares_io.reader import FolderReader
from api_iso_antares.custom_types import JSON


@pytest.mark.unit_test
def test_read_folder(
    lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    file_content = {"section": {"params": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content

    folder_reader = FolderReader(
        reader_ini=ini_reader, jsonschema=lite_jsonschema, root=lite_path
    )

    res = folder_reader.read(lite_path)

    assert res == lite_jsondata
    assert ini_reader.read.call_count == 6


@pytest.mark.unit_test
def test_validate(lite_jsondata: JSON, lite_jsonschema: JSON) -> None:

    folder_reader = FolderReader(
        reader_ini=Mock(), jsonschema=lite_jsonschema, root=Mock()
    )

    try:
        folder_reader.validate(lite_jsondata)
    except Exception as e:
        print(e)
        pytest.fail()
