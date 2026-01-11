# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import pytest
from sqlalchemy.dialects.postgresql.array import Any

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


def build_dataset(study_dir: Path) -> Path:
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
    ini_path.write_text(ini_content)
    return ini_path


def test_get(tmp_path: Path) -> None:
    study_dir = tmp_path.joinpath("my_study")
    study_dir.mkdir()
    ini_path = build_dataset(study_dir)

    expected_json: dict[str, Any] = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    node = IniFileNode(
        config=FileStudyTreeConfig(
            study_path=ini_path,
            path=ini_path,
            version=-1,
            areas={},
            outputs={},
            study_id="id",
        ),
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
        config=FileStudyTreeConfig(
            study_path=tmp_path.joinpath("archived", ini_path.name),
            path=tmp_path.joinpath("archived", ini_path.name),
            version=-1,
            areas={},
            outputs={},
            study_id="id",
            archive_path=zipped_path,
        ),
    )
    assert zipped_node.get([]) == expected_json
    assert zipped_node.get(["part2"]) == {"key_bool": True, "key_bool2": False}
    assert zipped_node.get(["part2", "key_bool"])


def test_get_depth(tmp_path: Path) -> None:
    study_dir = tmp_path.joinpath("my_study")
    study_dir.mkdir()
    ini_path = build_dataset(study_dir)

    expected_json: dict[str, Any] = {
        "part1": {},
        "part2": {},
    }
    node = IniFileNode(
        config=FileStudyTreeConfig(
            study_path=ini_path,
            path=ini_path,
            version=-1,
            areas={},
            outputs={},
            study_id="id",
        ),
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
        config=FileStudyTreeConfig(
            study_path=tmp_path.joinpath("archived", ini_path.name),
            path=tmp_path.joinpath("archived", ini_path.name),
            version=-1,
            areas={},
            outputs={},
            study_id="id",
            archive_path=zipped_path,
        ),
    )
    assert zipped_node.get(depth=1) == expected_json


def test_save(tmp_path: Path) -> None:
    ini_path = tmp_path.joinpath("test.ini")

    node = IniFileNode(
        config=FileStudyTreeConfig(
            study_path=tmp_path,
            path=ini_path,
            version=-1,
            study_id="id",
            areas={},
            outputs={},
        ),
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
    node = IniFileNode(
        config=FileStudyTreeConfig(
            study_path=tmp_path,
            path=ini_path,
            version=-1,
            study_id="id",
            areas={},
            outputs={},
        ),
    )
    expected_ruleset = {"key_float": 2.1, "key_int": 1, "key_str": "value1"}
    ruleset = node.get(url)
    assert ruleset == expected_ruleset


def create_ini_node(study_path: Path, ini_path: Path) -> IniFileNode:
    return IniFileNode(
        config=FileStudyTreeConfig(
            study_path=study_path,
            path=ini_path,
            version=-1,
            study_id="id",
            areas={},
            outputs={},
        ),
    )


def test_update_ignorecase(tmp_path: Path) -> None:
    ini_path = tmp_path.joinpath("test.ini")
    ini_content = textwrap.dedent(
        """\
        [sts_FR]
        key = 1
        """
    )
    ini_path.write_text(ini_content)
    node = create_ini_node(
        study_path=tmp_path,
        ini_path=ini_path,
    )
    node.save(data={"new_key": 3}, url=["sts_fr"])
    assert node.get() == {"sts_FR": {"new_key": 3}}

    node.save(data=4, url=["sts_fr", "new_key"])
    assert node.get() == {"sts_FR": {"new_key": 4}}

    node.save(data=5, url=["sts_fr", "other_key"])
    assert node.get() == {"sts_FR": {"new_key": 4, "other_key": 5}}


def test_delete_ignorecase(tmp_path: Path) -> None:
    ini_path = tmp_path.joinpath("test.ini")
    ini_content = textwrap.dedent(
        """\
        [sts_FR]
        Key = 1
        key2 = 3
        """
    )
    ini_path.write_text(ini_content)
    node = create_ini_node(
        study_path=tmp_path,
        ini_path=ini_path,
    )
    node.delete(url=["sts_fr", "key"])
    assert node.get() == {"sts_FR": {"key2": 3}}

    node.delete(url=["sts_fr"])
    assert node.get() == {}


def test_get_node(tmp_path: Path) -> None:
    ini_path = tmp_path.joinpath("test.ini")
    ini_content = textwrap.dedent(
        """\
        [sts_FR]
        Key = 1
        key2 = 3
        """
    )
    ini_path.write_text(ini_content)
    node = create_ini_node(
        study_path=tmp_path,
        ini_path=ini_path,
    )

    assert node.get_node() is node
    assert node.get_node_and_remainder(["sts_fr", "key2"]) == (node, ["sts_fr", "key2"])
