import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from jsonschema import ValidationError, validate  # type: ignore

from api_iso_antares.antares_io.reader import StudyReader

jsonschema_litteral = """
{
  "$id": "http://json-schema.org/draft-07/schema#",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "A small exemple.",
  "type": "object",
  "properties": {
    "part1": {
      "type": "object",
      "required": [
        "key_int",
        "key_str"
      ],
      "properties": {
        "key_int": {
          "type": "integer",
          "description": "A description"
        },
        "key_str": {
          "type": "string",
          "description": "An other description"
        }
      }
    },
    "part2": {
      "type": "object",
      "properties": {
        "key_bool": {
          "type": "boolean",
          "description": "A description"
        },
        "key_bool2": {
          "type": "boolean"
        }
      }
    }
  }
}
"""


@pytest.mark.unit_test
def test_validate_json_ok() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_validate_json_wrong_key() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"WRONG_KEY": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    with pytest.raises(ValidationError):
        validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_validate_json_wrong_type() -> None:
    jsonschema = json.loads(jsonschema_litteral)

    jsondata = {
        "part1": {"key_int": 1.9, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    with pytest.raises(ValidationError):
        validate(jsondata, jsonschema)


@pytest.mark.unit_test
def test_read() -> None:
    # Input
    path = Path("my-simulation")

    # Mock
    ini_reader = Mock()
    ini_reader.read = Mock(return_value={"section": {"parms": 123}})

    # Expected
    expected_data = {
        "settings": {"generaldata.ini": {"section": {"parms": 123}}}
    }

    # Test
    simulation_reader = StudyReader(reader_ini=ini_reader)
    res = simulation_reader.read(path)

    # Verify
    assert res == expected_data
    ini_reader.read.assert_called_once_with(path / "settings/generaldata.ini")


@pytest.mark.unit_test
def test_read_folder(tmp_path: str) -> None:

    """
    study1
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

    path = Path(tmp_path) / "study1"
    path_study = Path(path)
    path.mkdir()
    (path / "file1.ini").touch()
    path /= "folder1"
    path.mkdir()
    (path / "file2.ini").touch()
    (path / "matrice1.txt").touch()
    path /= "folder2"
    path.mkdir()
    (path / "matrice2.txt").touch()
    path = Path(path_study) / "folder3"
    path.mkdir()
    (path / "file3.ini").touch()

    file_content = {"section": {"parms": 123}}
    ini_reader = Mock()
    ini_reader.read.return_value = file_content

    study_reader = StudyReader(reader_ini=file_content)

    expected_json = {
        "file1.ini": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": "matrices/study1/folder1/matrice1.txt",
            "folder2": {
                "matrice2.txt": "matrices/study1/folder1/matrice2.txt",
            },
        },
        "folder3": {
            "file3.ini": file_content
        }
    }

    res = study_reader.read(path_study)
    assert res == expected_json


@pytest.mark.unit_test
def test_handle_folder_direct_depth():
    # Input
    parts = ('folder1', 'folder2')
    study = {'folder1': {}}

    # Expected
    exp = {'folder1': {'folder2': {}}}

    # Test & verify
    sub = StudyReader._handle_folder(parts, study)
    assert study == exp
    assert sub == {}


@pytest.mark.unit_test
def test_handle_folder_side_depth():
    # Input
    parts = ('folder3', )
    study = {'folder1': {'folder2': {}}}

    # Expected
    exp = {'folder1': {'folder2': {}}, 'folder3': {}}

    # Test & verify
    sub = StudyReader._handle_folder(parts, study)
    assert study == exp
    assert sub == {}

