# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

project_dir: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api_iso_antares.custom_types import JSON


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
        "$id": "http://example.com/example.json",
        "type": "object",
        "title": "The root schema",
        "required": ["file1.ini", "folder1", "folder3"],
        "properties": {
            "file1.ini": {
                "$id": "#/properties/file1.ini",
                "type": "object",
                "title": "The file1.ini schema",
                "properties": {
                    "section": {
                        "$id": "#/properties/file1.ini/properties/section",
                        "type": "object",
                        "required": ["parms"],
                        "properties": {
                            "parms": {
                                "$id": "#/properties/file1.ini/properties/section/properties/parms",
                                "type": "integer",
                                "title": "The parms schema",
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
                        "$id": "#/properties/folder1/properties/file2.ini",
                        "type": "object",
                        "title": "The file2.ini schema",
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "$id": "#/properties/folder1/properties/file2.ini/properties/section",
                                "type": "object",
                                "title": "The section schema",
                                "required": ["parms"],
                                "properties": {
                                    "parms": {
                                        "$id": "#/properties/folder1/properties/file2.ini/properties/section/properties/parms",
                                        "type": "integer",
                                        "title": "The parms schema",
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
                "title": "The folder3 schema",
                "required": ["file3.ini"],
                "properties": {
                    "file3.ini": {
                        "$id": "#/properties/folder3/properties/file3.ini",
                        "type": "object",
                        "title": "The file3.ini schema",
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "$id": "#/properties/folder3/properties/file3.ini/properties/section",
                                "type": "object",
                                "title": "The section schema",
                                "required": ["parms"],
                                "properties": {
                                    "parms": {
                                        "$id": "#/properties/folder3/properties/file3.ini/properties/section/properties/parms",
                                        "type": "integer",
                                        "title": "The parms schema",
                                    }
                                },
                            }
                        },
                    }
                },
            },
        },
    }
