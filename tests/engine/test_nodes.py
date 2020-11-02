from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.nodes import (
    MixFolderNode,
    IniFileNode,
    OnlyListNode,
    OutputFolderNode,
    OutputLinksNode,
    InputLinksNode,
)
from api_iso_antares.jsonschema import JsonSchema

content = 42


@pytest.mark.unit_test
def test_mix_folder_with_zones_list(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s1/areas"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S1"},
        "properties": {
            "list": {
                "type": "string",
            },
            "sets": {
                "type": "string",
            },
        },
        "additionalProperties": {"type": "string"},
    }
    expected = {
        "list": content,
        "sets": content,
        "fr": content,
        "de": content,
        "it": content,
        "es": content,
    }

    filenames = ["list.txt", "sets.ini"]

    mix_folder(path, jsm, expected, filenames)


@pytest.mark.unit_test
def test_mix_file_with_zones_list(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s3/input/bindingconstraints"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S3"},
        "properties": {
            "bindingconstraints": {
                "type": "number",
                "rte-metadata": {"filename": "bindingconstraints.ini"},
            }
        },
        "additionalProperties": {"type": "number"},
    }

    exp_data = {
        "bindingconstraints": content,
        "northern mesh": content,
        "southern mesh": content,
    }

    filenames = ["bindingconstraints.ini"]

    mix_folder(path, jsm, exp_data, filenames)


def mix_folder(path: Path, jsm: JSON, exp_data: JSON, filenames: List[str]):
    node_mock = Mock()
    node_mock.get_content.return_value = content
    node_mock.get_filename.side_effect = filenames
    factory = Mock()
    factory.build.return_value = node_mock

    node = MixFolderNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory,
    )
    json_data = node.get_content()

    assert json_data == exp_data


@pytest.mark.unit_test
def test_mix_keys_in_ini_file(project_path: str):
    path = (
        project_path
        / "tests/engine/resources/s2/input/bindingconstraints/bindingconstraints.ini"
    )
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "id": {"type": "string"},
                "enabled": {"type": "boolean"},
                "type": {"type": "string"},
                "operator": {"type": "string"},
            },
            "additionalProperties": {"type": "number"},
        },
    }

    node = IniFileNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=IniReader(),
        parent=None,
        node_factory=Mock(),
    )
    json_data = node.get_content()

    assert json_data["0"]["east%north"] == -1
    assert json_data["1"]["east%west"] == 1

    jsm_validator = JsmValidator(jsm=JsonSchema(jsm))
    jsm_validator.validate(json_data)


@pytest.mark.unit_test
def test_output_folder(project_path):
    path = project_path / "tests/engine/resources/s12/output"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S12"},
        "type": "object",
        "properties": {},
        "additionalProperties": {
            "type": "object",
            "properties": {
                "hello": {"type": "string"},
                "world": {"type": "string"},
            },
        },
    }

    exp_data = {
        "1": {
            "date": "19450623-0565",
            "type": "adequacy",
            "name": "",
            "hello": content,
        },
        "2": {
            "date": "20201009-1221",
            "type": "economy",
            "name": "hello-world",
            "hello": content,
            "world": content,
        },
    }

    node_mock = Mock()
    node_mock.get_content.return_value = content
    factory_mock = Mock()
    factory_mock.build.return_value = node_mock

    node = OutputFolderNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory_mock,
    )

    data = node.get_content()

    assert data == exp_data


@pytest.mark.unit_test
def test_dir_with_dynamic_ini_files(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s4/input/hydro/allocation"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S4"},
        "properties": {},
        "additionalProperties": {
            "type": "object",
            "properties": {
                "[allocation]": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": {"type": "number"},
                }
            },
        },
    }

    expected_json_data = {
        "east": content,
        "north": content,
        "south": content,
        "west": content,
    }

    only_list_node(path, jsm, expected_json_data)


@pytest.mark.unit_test
def test_dir_with_dynamic_multi_txt_files(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s6/capacity"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S6"},
        "properties": {},
        "additionalProperties": {"type": "string"},
    }

    expected_json_data = {
        "reservoir_de": content,
        "waterValues_de": content,
        "waterValues_it": content,
        "reservoir_it": content,
        "inflowPattern_fr": content,
        "maxpower_es": content,
        "maxpower_de": content,
        "maxpower_it": content,
        "creditmodulations_fr": content,
        "reservoir_es": content,
        "waterValues_es": content,
        "waterValues_fr": content,
        "reservoir_fr": content,
        "creditmodulations_es": content,
        "inflowPattern_it": content,
        "inflowPattern_de": content,
        "creditmodulations_de": content,
        "maxpower_fr": content,
        "inflowPattern_es": content,
        "creditmodulations_it": content,
    }

    only_list_node(path, jsm, expected_json_data)


@pytest.mark.unit_test
def test_set_of_temporality(project_path: Path):
    path = project_path / "tests/engine/resources/s9/de"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S9"},
        "type": "object",
        "additionalProperties": {"type": "number"},
    }

    content = 42

    exp_data = {
        "details-daily": content,
        "details-monthly": content,
        "id-daily": content,
        "id-monthly": content,
        "values-daily": content,
        "values-monthly": content,
    }

    only_list_node(path, jsm, exp_data)


@pytest.mark.unit_test
def test_set_of_scenarios(project_path: Path):
    path = project_path / "tests/engine/resources/s10/mc-ind"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S10"},
        "type": "object",
        "additionalProperties": {
            "type": "number",
        },
    }

    exp_data = {
        "00001": content,
        "00002": content,
        "00003": content,
    }

    only_list_node(path, jsm, exp_data)


def only_list_node(path: Path, jsm: JSON, exp_data: JSON):
    node_mock = Mock()
    node_mock.get_content.return_value = content
    factory_mock = Mock()
    factory_mock.build.return_value = node_mock

    node = OnlyListNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory_mock,
    )

    data = node.get_content()

    assert data == exp_data


@pytest.mark.unit_test
def test_set_of_output_link(project_path: Path):
    path = project_path / "tests/engine/resources/s15/links"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S15"},
        "type": "object",
        "properties": {},
        "additionalProperties": {
            "type": "object",
            "properties": {},
            "additionalProperties": {"type": "number"},
        },
    }

    exp_data = {
        "de": {"fr": content, "it": content},
        "es": {"fr": content},
        "fr": {"it": content},
    }

    node_mock = Mock()
    node_mock.get_content.return_value = content
    factory_mock = Mock()
    factory_mock.build.return_value = node_mock

    node = OutputLinksNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory_mock,
    )

    data = node.get_content()

    assert data == exp_data


@pytest.mark.unit_test
def test_set_of_input_link(project_path: Path):
    path = project_path / "tests/engine/resources/s14/links"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S14"},
        "type": "object",
        "properties": {},
        "additionalProperties": {
            "type": "object",
            "properties": {
                "properties": {
                    "type": "number",
                    "rte-metadata": {"filename": "properties.ini"},
                }
            },
            "additionalProperties": {"type": "number"},
        },
    }

    exp_data = {
        "de": {"fr": content, "properties": content},
        "es": {"fr": content, "properties": content},
        "fr": {"it": content, "properties": content},
        "it": {"properties": content},
    }

    node_mock = Mock()
    node_mock.get_content.return_value = content
    node_mock.get_filename.return_value = "properties.ini"
    factory_mock = Mock()
    factory_mock.build.return_value = node_mock

    node = InputLinksNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory_mock,
    )

    data = node.get_content()

    assert data == exp_data
