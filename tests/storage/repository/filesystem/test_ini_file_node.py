from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


def build_dataset(tmp_path: str) -> Tuple[Path, JSON]:
    path = Path(tmp_path) / "test.ini"
    ini_content = """
        [part1]
        key_int = 1
        key_float = 2.1
        key_str = value1

        [part2]
        key_bool = True
        key_bool2 = False
    """
    types = {
        "part1": {"key_int": int, "key_float": float, "key_str": str},
        "part2": {
            "key_bool": bool,
            "key_bool2": bool,
        },
    }
    path.write_text(ini_content)
    return path, types


@pytest.mark.unit_test
def test_get(tmp_path: str) -> None:
    path, types = build_dataset(tmp_path)

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(path, areas=dict(), outputs=dict(), study_id="id"),
        types=types,
    )
    assert node.get([]) == expected_json
    assert node.get(["part2"]) == {"key_bool": True, "key_bool2": False}
    assert node.get(["part2", "key_bool"])


@pytest.mark.unit_test
def test_get_depth(tmp_path: str) -> None:
    path, types = build_dataset(tmp_path)

    expected_json = {
        "part1": {},
        "part2": {},
    }
    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(path, areas=dict(), outputs=dict(), study_id="id"),
        types=types,
    )
    assert node.get(depth=1) == expected_json


@pytest.mark.unit_test
def test_validate_section():
    data = {"section": {"params": 42}}

    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(Path(), study_id="id"),
        types={"wrong-section": {}},
    )
    assert node.check_errors(data=data) == [
        "section wrong-section not in IniFileNode"
    ]
    with pytest.raises(ValueError):
        node.check_errors(data, raising=True)

    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(Path(), study_id="id"),
        types={"section": {"wrong-params": 42}},
    )
    assert node.check_errors(data=data) == [
        "param wrong-params of section section not in IniFileNode"
    ]
    with pytest.raises(ValueError):
        node.check_errors(data, raising=True)

    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(Path(), study_id="id"),
        types={"section": {"params": str}},
    )
    assert node.check_errors(data=data) == [
        "param params of section section in IniFileNode bad type"
    ]


@pytest.mark.unit_test
def test_save(tmp_path: str) -> None:
    path = Path(tmp_path) / "test.ini"

    ini_content = """[part1]
key_int = 1
key_float = 2.1
key_str = value1
    """
    path.write_text(ini_content)

    exp = """[part1]
key_int = 10
key_str = value10
key_float = 3.14

"""

    types = {"part1": {"key_int": int, "key_float": float, "key_str": str}}

    node = IniFileNode(
        context=Mock(),
        config=StudyConfig(path, study_id="id", areas=dict(), outputs=dict()),
        types=types,
    )
    data = {
        "part1": {"key_int": 10, "key_str": "value10", "key_float": 2.1},
    }
    node.save(data)
    node.save(3.14, url=["part1", "key_float"])
    assert exp == path.read_text()
