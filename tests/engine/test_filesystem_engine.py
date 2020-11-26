from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.jsm import JsonSchema


def get_mocked_filesystem_engine(ini_cleaner: Callable) -> FileSystemEngine:

    file_content = {"section": {"params": 123}}

    ini_reader = Mock()
    ini_reader.read.return_value = file_content

    ini_writer = Mock()
    ini_writer.write = lambda data, path: path.touch()

    matrix_writer = Mock()
    matrix_writer.write = lambda data, path: path.touch()

    readers = {"default": ini_reader}
    writers = {"default": ini_writer, "matrix": matrix_writer}

    filesystem_engine = FileSystemEngine(readers=readers, writers=writers)

    return filesystem_engine


@pytest.mark.unit_test
def test_read_filesystem(
    lite_path: Path,
    lite_jsonschema: JSON,
    lite_jsondata: JSON,
    ini_cleaner: Callable,
) -> None:

    folder_reader = get_mocked_filesystem_engine(ini_cleaner)

    res = folder_reader.parse(lite_path, jsm=JsonSchema(lite_jsonschema))
    ini_reader = folder_reader.get_reader()

    assert res == lite_jsondata
    assert ini_reader.read.call_count == 6


@pytest.mark.unit_test
def test_read_sub_study(
    lite_path: Path,
    lite_jsonschema: JSON,
    lite_jsondata: JSON,
    ini_cleaner: Callable,
) -> None:
    # Input
    path = lite_path / "folder1/folder2"
    jsm = JsonSchema(lite_jsonschema).get_child("folder1").get_child("folder2")

    # Expected
    exp_reader_path = lite_path / "folder1/folder2"

    fs_engine = get_mocked_filesystem_engine(ini_cleaner)

    res = fs_engine.parse(deep_path=path, study_path=lite_path, jsm=jsm)
    ini_reader = fs_engine.get_reader()

    assert res == lite_jsondata["folder1"]["folder2"]


@pytest.mark.unit_test
def test_read_sub_study_inside_ini(
    lite_path: Path,
    lite_jsonschema: JSON,
    lite_jsondata: JSON,
    ini_cleaner: Callable,
) -> None:
    # Input
    path = lite_path / "folder1/file2.ini"
    jsm = JsonSchema(lite_jsonschema)\
        .get_child("folder1")\
        .get_child("file2")\
        .get_child("section")\
        .get_child("params")

    fs_engine = get_mocked_filesystem_engine(ini_cleaner)

    res = fs_engine.parse(deep_path=path, study_path=lite_path, jsm=jsm, keys="section/params")
    ini_reader = fs_engine.get_reader()

    assert res == lite_jsondata["folder1"]["file2"]["section"]["params"]


@pytest.mark.unit_test
def test_write_filesystem(
    tmp_path,
    lite_path: Path,
    lite_jsonschema: JSON,
    lite_jsondata: JSON,
    ini_cleaner: Callable,
) -> None:

    filesystem_engine = get_mocked_filesystem_engine(ini_cleaner)

    study_name_destination = "copy_of_lite_study"
    write_path = Path(tmp_path) / study_name_destination
    filesystem_engine.write(write_path, lite_jsondata)

    study_name_source = lite_path.parts[-1]
    data_source = filesystem_engine.parse(lite_path)
    data_destination = filesystem_engine.parse(write_path)

    def replace_study_name(data: JSON) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("file/"):
                    data[key] = value.replace(
                        study_name_destination, study_name_source
                    )
                else:
                    replace_study_name(value)

    replace_study_name(data_destination)

    assert data_destination == data_source
