import json
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest
from jsonschema import ValidationError, validate

from api_iso_antares.antares_io.reader import FolderReader
from api_iso_antares.custom_types import JSON


@pytest.mark.unit_test
def test_read_folder(tmp_path: str, lite_jsonschema: JSON) -> None:
    """
    root1
    |
    _ file1.ini
    |_folder1
        |_ file2.ini
        |_ matrice1.txt
        |_ folder2
            |_ matrice2.txt
    |_folder3
        |_ file3.ini
    """

    # Input
    path = Path(tmp_path) / "root1"
    path_folder = Path(path)
    path.mkdir()
    (path / "file1.ini").touch()
    path /= "folder1"
    path.mkdir()
    (path / "file2.ini").touch()
    (path / "matrice1.txt").touch()
    path /= "folder2"
    path.mkdir()
    (path / "matrice2.txt").touch()
    path = Path(path_folder) / "folder3"
    path.mkdir()
    (path / "file3.ini").touch()

    file_content = {"section": {"parms": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content

    folder_reader = FolderReader(
        reader_ini=ini_reader, jsonschema=lite_jsonschema, root=Path(tmp_path)
    )

    expected_json = {
        "file1.ini": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": str(Path("matrices/root1/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(
                    Path("matrices/root1/folder1/folder2/matrice2.txt")
                ),
            },
        },
        "folder3": {"file3.ini": file_content},
    }

    res = folder_reader.read(path_folder)
    assert res == expected_json
    assert ini_reader.read.call_count == 3


@pytest.mark.unit_test
def test_validate(lite_jsonschema: JSON) -> None:
    file_content = {"section": {"parms": 123}}
    folder_json = {
        "file1.ini": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": str(Path("matrices/root1/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(
                    Path("matrices/root1/folder1/folder2/matrice2.txt")
                ),
            },
        },
        "folder3": {"file3.ini": file_content},
    }

    folder_reader = FolderReader(
        reader_ini=Mock(), jsonschema=lite_jsonschema, root=Mock()
    )

    try:
        folder_reader.validate(folder_json)
    except Exception:
        pytest.fail()
