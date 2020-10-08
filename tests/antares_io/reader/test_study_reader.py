import json
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest
from jsonschema import ValidationError, validate  # type: ignore

from api_iso_antares.antares_io.reader import StudyReader
from api_iso_antares.custom_types import JSON

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

    study_reader = StudyReader(reader_ini=ini_reader, jsonschema={})

    expected_json = {
        "file1.ini": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": str(Path("matrices/study1/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(
                    Path("matrices/study1/folder1/folder2/matrice2.txt")
                ),
            },
        },
        "folder3": {"file3.ini": file_content},
    }

    res = study_reader.read(path_study, do_validate=False)
    assert res == expected_json
    assert ini_reader.read.call_count == 3


@pytest.mark.unit_test
def test_handle_folder_direct_depth() -> None:
    # Input
    parts: Tuple[str, ...] = ("folder1", "folder2")
    study: JSON = {"folder1": {}}

    # Expected
    exp: JSON = {"folder1": {"folder2": {}}}

    # Test & verify
    sub = StudyReader._handle_folder(parts, study)
    assert study == exp
    assert sub == {}


@pytest.mark.unit_test
def test_handle_folder_side_depth() -> None:
    # Input
    parts = ("folder3",)
    study: JSON = {"folder1": {"folder2": {}}}

    # Expected
    exp = {"folder1": {"folder2": {}}, "folder3": {}}

    # Test & verify
    sub = StudyReader._handle_folder(parts, study)
    assert study == exp
    assert sub == {}


@pytest.mark.unit_test
def test_validate() -> None:

    file_content = {"section": {"parms": 123}}
    study_json = {
        "file1.ini": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": str(Path("matrices/study1/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(
                    Path("matrices/study1/folder1/folder2/matrice2.txt")
                ),
            },
        },
        "folder3": {"file3.ini": file_content},
    }

    jsonschema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "object",
        "title": "The root schema",
        "description": "The root schema comprises the entire JSON document.",
        "required": [],
        "properties": {
            "file1.ini": {
                "$id": "#/properties/file1.ini",
                "type": "object",
                "title": "The file1.ini schema",
                "description": "An explanation about the purpose of this instance.",
                "required": [],
                "properties": {
                    "section": {
                        "$id": "#/properties/file1.ini/properties/section",
                        "type": "object",
                        "title": "The section schema",
                        "description": "An explanation about the purpose of this instance.",
                        "required": [],
                        "properties": {
                            "parms": {
                                "$id": "#/properties/file1.ini/properties/section/properties/parms",
                                "type": "integer",
                                "title": "The parms schema",
                                "description": "An explanation about the purpose of this instance.",
                            }
                        },
                    }
                },
            },
            "folder1": {
                "$id": "#/properties/folder1",
                "type": "object",
                "title": "The folder1 schema",
                "description": "An explanation about the purpose of this instance.",
                "required": [],
                "properties": {
                    "file2.ini": {
                        "$id": "#/properties/folder1/properties/file2.ini",
                        "type": "object",
                        "title": "The file2.ini schema",
                        "description": "An explanation about the purpose of this instance.",
                        "required": [],
                        "properties": {
                            "section": {
                                "$id": "#/properties/folder1/properties/file2.ini/properties/section",
                                "type": "object",
                                "title": "The section schema",
                                "description": "An explanation about the purpose of this instance.",
                                "required": [],
                                "properties": {
                                    "parms": {
                                        "$id": "#/properties/folder1/properties/file2.ini/properties/section/properties/parms",
                                        "type": "integer",
                                        "title": "The parms schema",
                                        "description": "An explanation about the purpose of this instance.",
                                    }
                                },
                            }
                        },
                    },
                    "matrice1.txt": {
                        "$id": "#/properties/folder1/properties/matrice1.txt",
                        "type": "string",
                        "title": "The matrice1.txt schema",
                        "description": "An explanation about the purpose of this instance.",
                    },
                    "folder2": {
                        "$id": "#/properties/folder1/properties/folder2",
                        "type": "object",
                        "title": "The folder2 schema",
                        "description": "An explanation about the purpose of this instance.",
                        "required": [],
                        "properties": {
                            "matrice2.txt": {
                                "$id": "#/properties/folder1/properties/folder2/properties/matrice2.txt",
                                "type": "string",
                                "title": "The matrice2.txt schema",
                                "description": "An explanation about the purpose of this instance.",
                            }
                        },
                    },
                },
            },
            "folder3": {
                "$id": "#/properties/folder3",
                "type": "object",
                "title": "The folder3 schema",
                "description": "An explanation about the purpose of this instance.",
                "required": [],
                "properties": {
                    "file3.ini": {
                        "$id": "#/properties/folder3/properties/file3.ini",
                        "type": "object",
                        "title": "The file3.ini schema",
                        "description": "An explanation about the purpose of this instance.",
                        "required": [],
                        "properties": {
                            "section": {
                                "$id": "#/properties/folder3/properties/file3.ini/properties/section",
                                "type": "object",
                                "title": "The section schema",
                                "description": "An explanation about the purpose of this instance.",
                                "required": [],
                                "properties": {
                                    "parms": {
                                        "$id": "#/properties/folder3/properties/file3.ini/properties/section/properties/parms",
                                        "type": "integer",
                                        "title": "The parms schema",
                                        "description": "An explanation about the purpose of this instance.",
                                    }
                                },
                            }
                        },
                    }
                },
            },
        },
    }

    study_reader = StudyReader(reader_ini=None, jsonschema=jsonschema)

    try:
        study_reader.validate(study_json)
    except Exception:
        pytest.fail()
