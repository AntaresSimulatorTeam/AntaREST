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

from collections.abc import Callable
from pathlib import Path

from antarest.core.serde.ini_common import any_section_option_matcher
from antarest.core.serde.ini_reader import IniReader
from antarest.core.serde.ini_writer import LOWER_CASE_SERIALIZER, IniWriter


def test_lower_case_serializer() -> None:
    assert LOWER_CASE_SERIALIZER("Hello") == "hello"


def test_write(tmp_path: str, ini_cleaner: Callable[[str], str]) -> None:
    path = Path(tmp_path) / "test.ini"

    ini_content = """
        [part]
        key_int = 1
        key_float = 2.1
        key_str = value1
        
        [partWithCapitals]
        key_bool = True
        key_bool2 = False
        keyWithCapital = True
        
        [partWithSameKey]
        key = value1
        key = value2
        key = value3
        key2 = 4,2
        key2 = 1,3
        key3 = [1, 2, 3]
    """

    json_data = {
        "part": {"key_int": 1, "key_float": 2.1, "key_str": "value1"},
        "partWithCapitals": {
            "key_bool": True,
            "key_bool2": False,
            "keyWithCapital": True,
        },
        "partWithSameKey": {
            "key": ["value1", "value2", "value3"],
            "key2": ["4,2", "1,3"],
            "key3": [1, 2, 3],
        },
    }
    writer = IniWriter(special_keys=["key", "key2"])
    writer.write(json_data, path)

    assert ini_cleaner(ini_content) == ini_cleaner(path.read_text())


def test_write_with_custom_serializer(tmp_path: str, ini_cleaner: Callable[[str], str]) -> None:
    path = Path(tmp_path) / "test.ini"

    def duplicate(value: str) -> str:
        return value * 2

    serializers = {any_section_option_matcher("group"): duplicate}
    writer = IniWriter(value_serializers=serializers)

    expected = """
        [part1]
        group = GasGas

        [part2]
        group = GasGas

        [part3]
        other = Gas
    """

    json_data = {
        "part1": {"group": "Gas"},
        "part2": {"group": "Gas"},
        "part3": {"other": "Gas"},
    }
    writer.write(json_data, path)

    assert ini_cleaner(path.read_text()) == ini_cleaner(expected)


def test_write_repeating_sections__nominal_case(tmp_path: str, ini_cleaner: Callable[[str], str]) -> None:
    path = Path(tmp_path) / "reserves.ini"

    expected = """
        [Reserve 1]
        cluster-name = cluster1
        max-power = 20
        max-power-off = 10
        participation-cost = 1
        participation-cost-off = 2

        [Reserve 1]
        cluster-name = cluster2
        max-power = 20
        max-power-off = 10
        participation-cost = 1
        participation-cost-off = 2

        [Reserve 2]
        cluster-name = cluster1
        max-power = 30
    """

    data = [
        (
            "Reserve 1",
            {
                "cluster-name": "cluster1",
                "max-power": 20,
                "max-power-off": 10,
                "participation-cost": 1,
                "participation-cost-off": 2,
            },
        ),
        (
            "Reserve 1",
            {
                "cluster-name": "cluster2",
                "max-power": 20,
                "max-power-off": 10,
                "participation-cost": 1,
                "participation-cost-off": 2,
            },
        ),
        (
            "Reserve 2",
            {"cluster-name": "cluster1", "max-power": 30},
        ),
    ]
    IniWriter().write_repeating_sections(data, path)

    assert ini_cleaner(path.read_text()) == ini_cleaner(expected)


def test_write_repeating_sections__round_trip(tmp_path: str) -> None:
    path = Path(tmp_path) / "reserves.ini"
    data: list[tuple[str, dict]] = [
        ("Reserve 1", {"cluster-name": "cluster1", "max-power": 20}),
        ("Reserve 1", {"cluster-name": "cluster2", "max-power": 30}),
        ("symmetries", {"cluster1": "[Reserve1, Reserve2]"}),
    ]

    IniWriter().write_repeating_sections(data, path)
    actual = IniReader().read_repeating_sections(path)

    assert actual == data


def test_write_repeating_sections__empty_list_writes_empty_file(tmp_path: str) -> None:
    path = Path(tmp_path) / "reserves.ini"
    IniWriter().write_repeating_sections([], path)

    assert path.read_text() == ""
