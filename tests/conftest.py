# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

project_dir: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api_iso_antares.custom_types import JSON


@pytest.fixture
def project_path() -> Path:
    return project_dir


@pytest.fixture
def test_json_data() -> JSON:
    json_data = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    return json_data


@pytest.fixture
def lite_jsonschema() -> JSON:
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "properties": {
            "key_file1": {
                "type": "object",
                "rte-metadata": {"filename": "file1.ini"},
                "properties": {
                    "section": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "integer",
                                "title": "The params schema",
                            }
                        },
                    }
                },
            },
            "folder1": {
                "$id": "#/properties/folder1",
                "type": "object",
                "title": "The folder1 schema",
                "required": ["file2.ini", "matrice1.txt", "folder2"],
                "properties": {
                    "file2.ini": {
                        "type": "object",
                        "title": "The file3.ini schema",
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "type": "object",
                                "title": "The section schema",
                                "required": ["params"],
                                "properties": {
                                    "params": {
                                        "type": "integer",
                                        "title": "The params schema",
                                    }
                                },
                            }
                        },
                    },
                    "matrice1.txt": {
                        "$id": "#/properties/folder1/properties/matrice1.txt",
                        "type": "string",
                        "title": "The matrice1.txt schema",
                    },
                    "folder2": {
                        "$id": "#/properties/folder1/properties/folder2",
                        "type": "object",
                        "title": "The folder2 schema",
                        "required": ["matrice2.txt"],
                        "properties": {
                            "matrice2.txt": {
                                "$id": "#/properties/folder1/properties/folder2/properties/matrice2.txt",
                                "type": "string",
                                "title": "The matrice2.txt schema",
                            }
                        },
                    },
                },
            },
            "folder3": {
                "$id": "#/properties/folder3",
                "type": "object",
                "required": ["file3.ini"],
                "properties": {
                    "file3.ini": {
                        "type": "object",
                        "title": "The file3.ini schema",
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "type": "object",
                                "title": "The section schema",
                                "required": ["params"],
                                "properties": {
                                    "params": {
                                        "type": "integer",
                                        "title": "The params schema",
                                    }
                                },
                            }
                        },
                    },
                    "areas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "$id": {"type": "string"},
                                "matrice1.txt": {
                                    "type": "string",
                                },
                                "file4.ini": {
                                    "type": "object",
                                    "required": ["section"],
                                    "properties": {
                                        "section": {
                                            "type": "object",
                                            "required": ["params"],
                                            "properties": {
                                                "params": {
                                                    "type": "integer",
                                                }
                                            },
                                        }
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def lite_jsondata() -> JSON:
    file_content = {"section": {"params": 123}}
    return {
        "key_file1": file_content,
        "folder1": {
            "file2.ini": file_content,
            "matrice1.txt": str(Path("file/folder1/matrice1.txt")),
            "folder2": {
                "matrice2.txt": str(Path("file/folder1/folder2/matrice2.txt")),
            },
        },
        "folder3": {
            "file3.ini": file_content,
            "areas": [
                {
                    "$id": "area1",
                    "matrice1.txt": str(
                        Path("file/folder3/areas/area1/matrice1.txt")
                    ),
                    "file4.ini": file_content,
                },
                {
                    "$id": "area2",
                    "matrice1.txt": str(
                        Path("file/folder3/areas/area2/matrice1.txt")
                    ),
                    "file4.ini": file_content,
                },
                {
                    "$id": "area3",
                    "matrice1.txt": str(
                        Path("file/folder3/areas/area3/matrice1.txt")
                    ),
                    "file4.ini": file_content,
                },
            ],
        },
    }


@pytest.fixture
def lite_path(tmp_path: Path) -> Path:
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
        |_ areas
            |_ area1
                |_ matrice3.txt
                |_ file4.ini
            |_ area2
                |_ matrice3.txt
                |_ file4.ini
            |_ area3
                |_ matrice3.txt
                |_ file4.ini
    """

    str_content_ini = """
        [section]
        params = 123
    """

    path = Path(tmp_path) / "root1"
    path_folder = Path(path)
    path_folder.mkdir()
    (path / "file1.ini").write_text(str_content_ini)
    path /= "folder1"
    path.mkdir()
    (path / "file2.ini").write_text(str_content_ini)
    (path / "matrice1.txt").touch()
    path /= "folder2"
    path.mkdir()
    (path / "matrice2.txt").touch()
    path = Path(path_folder) / "folder3"
    path.mkdir()
    (path / "file3.ini").write_text(str_content_ini)

    path /= "areas"
    path.mkdir()

    def create_area(path_areas: Path, area: str) -> None:
        path_area = path_areas / area
        path_area.mkdir()
        (path_area / "file4.ini").write_text(str_content_ini)
        (path_area / "matrice1.txt").touch()

    create_area(path, "area1")
    create_area(path, "area2")
    create_area(path, "area3")

    return path_folder
