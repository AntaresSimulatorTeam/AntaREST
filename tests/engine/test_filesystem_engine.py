from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.jsm import JsonSchema


@pytest.mark.unit_test
def test_read_filesystem(
    lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    file_content = {"section": {"params": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content
    ini_writer = Mock()

    readers = {"default": ini_reader}
    writers = {"default": ini_writer}
    jsm = JsonSchema(lite_jsonschema)
    folder_reader = FileSystemEngine(jsm=jsm, readers=readers, writers=writers)

    res = folder_reader.parse(lite_path)

    assert res == lite_jsondata
    assert ini_reader.read.call_count == 6


@pytest.mark.unit_test
def test_write_filesystem(
    tmp_path: str, lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    file_content = {"section": {"params": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content
    ini_writer = Mock()

    readers = {"default": ini_reader}
    writers = {"default": ini_writer}
    jsm = JsonSchema(lite_jsonschema)

    folder_reader = FileSystemEngine(jsm=jsm, readers=readers, writers=writers)

    writed_path = Path(tmp_path)
    folder_reader.write(writed_path, lite_jsondata)

    assert folder_reader.parse(lite_path) == folder_reader.parse(writed_path)
