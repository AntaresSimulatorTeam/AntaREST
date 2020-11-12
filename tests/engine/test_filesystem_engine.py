from pathlib import Path
from unittest.mock import Mock

import pytest
import random
import string

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
    tmpdir_factory, lite_path: Path, lite_jsonschema: JSON, lite_jsondata: JSON
) -> None:

    # TODO

    file_content = {"section": {"params": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content
    ini_writer = Mock()

    readers = {"default": ini_reader}
    writers = {"default": ini_writer}
    jsm = JsonSchema(lite_jsonschema)

    folder_reader = FileSystemEngine(jsm=jsm, readers=readers, writers=writers)

    unique_path = Path(
        tmpdir_factory.getbasetemp()
        / "".join(random.choices(string.ascii_uppercase + string.digits, k=30))
    )
    unique_path.mkdir()
    write_path = unique_path / "root1"
    folder_reader.write(write_path, lite_jsondata)

    assert folder_reader.parse(lite_path) == folder_reader.parse(write_path)
