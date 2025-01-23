# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import shutil
import textwrap
import typing as t
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.model import JSON
from antarest.study.model import STUDY_VERSION_9_1
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    NAME_TO_ID_MATCHER,
    IniFileNode,
    SectionMatcher,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.scenariobuilder import ScenarioBuilder


def build_dataset(study_dir: Path) -> t.Tuple[Path, JSON]:
    ini_path = study_dir.joinpath("test.ini")
    ini_content = textwrap.dedent(
        """\
        [part1]
        key_int = 1
        key_float = 2.1
        key_str = value1

        [part2]
        key_bool = True
        key_bool2 = False
        """
    )
    section_types = {
        "part1": {
            "key_int": int,
            "key_float": float,
            "key_str": str,
        },
        "part2": {
            "key_bool": bool,
            "key_bool2": bool,
        },
    }
    ini_path.write_text(ini_content)
    return ini_path, section_types


@pytest.mark.unit_test
def test_get(tmp_path: Path) -> None:
    study_dir = tmp_path.joinpath("my_study")
    study_dir.mkdir()
    ini_path, types = build_dataset(study_dir)

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=ini_path,
            path=ini_path,
            version=-1,
            areas={},
            outputs={},
            study_id="id",
        ),
        types=types,
    )
    assert node.get([]) == expected_json
    assert node.get(["part2"]) == {"key_bool": True, "key_bool2": False}
    assert node.get(["part2", "key_bool"])

    base_name = str(tmp_path.joinpath("archived"))
    zipped_path = Path(
        shutil.make_archive(
            base_name,
            format="zip",
            root_dir=study_dir,
        )
    )

    zipped_node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path.joinpath("archived", ini_path.name),
            path=tmp_path.joinpath("archived", ini_path.name),
            version=-1,
            areas={},
            outputs={},
            study_id="id",
            archive_path=zipped_path,
        ),
        types=types,
    )
    assert zipped_node.get([]) == expected_json
    assert zipped_node.get(["part2"]) == {"key_bool": True, "key_bool2": False}
    assert zipped_node.get(["part2", "key_bool"])


@pytest.mark.unit_test
def test_get_depth(tmp_path: Path) -> None:
    study_dir = tmp_path.joinpath("my_study")
    study_dir.mkdir()
    ini_path, types = build_dataset(study_dir)

    expected_json = {
        "part1": {},
        "part2": {},
    }
    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=ini_path,
            path=ini_path,
            version=-1,
            areas={},
            outputs={},
            study_id="id",
        ),
        types=types,
    )
    assert node.get(depth=1) == expected_json

    base_name = str(tmp_path.joinpath("archived"))
    zipped_path = Path(
        shutil.make_archive(
            base_name,
            format="zip",
            root_dir=study_dir,
        )
    )

    zipped_node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path.joinpath("archived", ini_path.name),
            path=tmp_path.joinpath("archived", ini_path.name),
            version=-1,
            areas={},
            outputs={},
            study_id="id",
            archive_path=zipped_path,
        ),
        types=types,
    )
    assert zipped_node.get(depth=1) == expected_json


@pytest.mark.unit_test
def test_validate_section():
    data = {"section": {"params": 42}}

    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=Path(), path=Path(), version=-1, study_id="id"),
        types={"wrong-section": {}},
    )
    assert node.check_errors(data=data) == ["section wrong-section not in IniFileNode"]
    with pytest.raises(ValueError):
        node.check_errors(data, raising=True)

    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=Path(), path=Path(), version=-1, study_id="id"),
        types={"section": {"wrong-params": 42}},
    )
    assert node.check_errors(data=data) == ["param wrong-params of section section not in IniFileNode"]
    with pytest.raises(ValueError):
        node.check_errors(data, raising=True)

    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=Path(), path=Path(), version=-1, study_id="id"),
        types={"section": {"params": str}},
    )
    assert node.check_errors(data=data) == ["param params of section section in IniFileNode bad type"]


@pytest.mark.unit_test
def test_save(tmp_path: Path) -> None:
    ini_path = tmp_path.joinpath("test.ini")

    types = {
        "part1": {
            "key_int": int,
            "key_float": float,
            "key_str": str,
            "key_bool": bool,
        },
        "part2": {
            "key_int": int,
            "key_float": float,
            "key_str": str,
            "key_bool": bool,
        },
    }

    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path,
            path=ini_path,
            version=-1,
            study_id="id",
            areas={},
            outputs={},
        ),
        types=types,
    )

    # The example below allows for creating an INI file from scratch by providing
    # a dictionary of sections to write. The dictionary order is preserved.
    data = {
        "part1": {
            "key_float": 2.1,
            "key_int": 1,
            "key_str": "value1",
        },
        "part2": {
            "key_float": 18,
            "key_int": 5,
            "key_str": "value2",
        },
    }
    node.save(data)
    expected = textwrap.dedent(
        """\
        [part1]
        key_float = 2.1
        key_int = 1
        key_str = value1

        [part2]
        key_float = 18
        key_int = 5
        key_str = value2
        """
    )
    assert ini_path.read_text().strip() == expected.strip()

    # The example below allows for updating the parameters of a **section** in an INI file.
    # The update simply involves replacing all the parameters with the values defined
    # in the key/value dictionary. The previous values are removed, and new values can be added.
    # Note: this update only affects a specific section, leaving other sections unaffected.
    data = {
        # "key_int": 10,  # <- removed
        "key_str": "value10",
        "key_float": 2.1,
        "key_bool": True,  # <- inserted
    }
    node.save(data, url=["part1"])
    # note: the order of the keys is preserved in the output
    expected = textwrap.dedent(
        """\
        [part1]
        key_str = value10
        key_float = 2.1
        key_bool = True

        [part2]
        key_float = 18
        key_int = 5
        key_str = value2
        """
    )
    assert ini_path.read_text().strip() == expected.strip()

    # The exemple below allows for updating a single parameter, the others are unaffected.
    node.save(3.14, url=["part1", "key_float"])
    expected = textwrap.dedent(
        """\
        [part1]
        key_str = value10
        key_float = 3.14
        key_bool = True

        [part2]
        key_float = 18
        key_int = 5
        key_str = value2
        """
    )
    assert ini_path.read_text().strip() == expected.strip()


def _ini_node(tmp_path: Path, data: JSON = None, section_matcher: SectionMatcher = None) -> IniFileNode:
    ini_path = tmp_path.joinpath("test.ini")
    data = data or {
        "part1": {
            "key_float": 2.1,
            "key_int": 1,
            "key_str": "value1",
        },
        "part2": {
            "key_float": 18,
            "key_int": 5,
            "key_str": "value2",
        },
    }
    IniWriter().write(data=data, path=ini_path)

    node = IniFileNode(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path,
            path=ini_path,
            version=-1,
            study_id="id",
            areas={},
            outputs={},
        ),
        section_matcher=section_matcher,
    )
    return node


@pytest.fixture
def ini_node(tmp_path: Path) -> IniFileNode:
    return _ini_node(tmp_path)


@pytest.fixture
def ini_node_with_id_matching(tmp_path: Path) -> IniFileNode:
    return _ini_node(tmp_path, section_matcher=NAME_TO_ID_MATCHER)


@pytest.mark.unit_test
def test_delete_section(ini_node: IniFileNode) -> None:
    ini_node.delete(["Part1"])
    assert ini_node.get() == {
        "part2": {
            "key_float": 18,
            "key_int": 5,
            "key_str": "value2",
        },
    }


@pytest.mark.unit_test
def test_delete_section_with_matching(ini_node_with_id_matching: IniFileNode) -> None:
    ini_node = ini_node_with_id_matching
    ini_node.delete(["Part1"])
    assert ini_node.get() == {
        "part2": {
            "key_float": 18,
            "key_int": 5,
            "key_str": "value2",
        },
    }


@pytest.mark.unit_test
def test_delete_section_with_matching_2(tmp_path: Path) -> None:
    ini_node = _ini_node(
        tmp_path, section_matcher=NAME_TO_ID_MATCHER, data={"Grand'Maison": {"key_float": 18, "key_int": 5}}
    )
    ini_node.delete(["grand maison"])
    assert ini_node.get() == {}


@pytest.mark.unit_test
def test_get_section_with_matching(tmp_path: Path) -> None:
    ini_node = _ini_node(
        tmp_path, section_matcher=NAME_TO_ID_MATCHER, data={"Grand'Maison": {"key_float": 18, "key_int": 5}}
    )
    ini_node.get(["grand maison"])
    assert ini_node.get() == {"Grand'Maison": {"key_float": 18, "key_int": 5}}


@pytest.mark.unit_test
def test_delete_option(ini_node: IniFileNode) -> None:
    ini_node.delete(["part1", "key_int"])
    assert ini_node.get() == {
        "part1": {
            "key_float": 2.1,
            "key_str": "value1",
        },
        "part2": {
            "key_float": 18,
            "key_int": 5,
            "key_str": "value2",
        },
    }


@pytest.mark.unit_test
def test_delete_file(ini_node: IniFileNode) -> None:
    ini_node.delete()
    assert ini_node.get() == {}


@pytest.mark.parametrize(
    ("ini_section", "url"),
    [
        ("default ruleset", ["default ruleset"]),
        ("default ruleset", ["Default Ruleset"]),
        ("Default Ruleset", ["default ruleset"]),
        ("Default Ruleset", ["Default Ruleset"]),
    ],
)
def test_get_scenario_builder(tmp_path: Path, ini_section: str, url: t.List[str]) -> None:
    ini_path = tmp_path.joinpath("test.ini")
    ini_content = textwrap.dedent(
        f"""\
        [{ini_section}]
        key_int = 1
        key_float = 2.1
        key_str = value1

        [Other ruleset]
        key_bool = True
        key_bool2 = False
        """
    )
    ini_path.write_text(ini_content)
    node = ScenarioBuilder(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=tmp_path,
            path=ini_path,
            version=STUDY_VERSION_9_1,
            study_id="id",
            areas={},
            outputs={},
        ),
    )
    expected_ruleset = {"key_float": 2.1, "key_int": 1, "key_str": "value1"}
    ruleset = node.get(url)
    assert ruleset == expected_ruleset
