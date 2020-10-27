from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.engine.nodes import (
    MixFolderNode,
    IniFileNode,
    NodeFactory,
    OnlyListNode,
    OutputFolderNode,
)
from api_iso_antares.jsonschema import JsonSchema


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
    content = "Hello, World"
    expected = {
        "list": content,
        "sets": content,
        "fr": content,
        "de": content,
        "it": content,
        "es": content,
    }

    node = Mock()
    node.get_content.return_value = content
    node.get_filename.side_effect = ["list.txt", "sets.ini"]
    factory = Mock()
    factory.build.return_value = node

    node = MixFolderNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory,
    )
    json_data = node.get_content()

    assert expected == json_data


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
def test_mix_file_with_zones_list(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s3/input/bindingconstraints"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S3"},
        "properties": {
            "bindingconstraints": {
                "rte-metadata": {"filename": "bindingconstraints.ini"},
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
        },
        "additionalProperties": {"type": "string"},
    }

    node = MixFolderNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=NodeFactory({"default": IniReader()}),
    )
    json_data = node.get_content()

    assert json_data["northern mesh.txt"] == str(
        Path("file/bindingconstraints/northern mesh.txt")
    )


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

    content = 42

    expected_json_data = {
        "east": content,
        "north": content,
        "south": content,
        "west": content,
    }

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
    json_data = node.get_content()

    assert json_data == expected_json_data


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

    content = "Hello, World"

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
    json_data = node.get_content()

    assert json_data == expected_json_data


@pytest.mark.unit_test
def test_output_folder(project_path):
    path = project_path / "tests/engine/resources/s8/output"

    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "rte-metadata": {"strategy": "S8"},
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

    content = 42

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

    content = 42

    exp_data = {
        "00001": content,
        "00002": content,
        "00003": content,
    }

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
