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

from pathlib import Path
from typing import Callable

import pytest

from antarest.core.serde.ini_common import any_section_option_matcher
from antarest.core.serde.ini_writer import LOWER_CASE_SERIALIZER, IniWriter


@pytest.mark.unit_test
def test_lower_case_serializer() -> None:
    assert LOWER_CASE_SERIALIZER("Hello") == "hello"


@pytest.mark.unit_test
def test_write(tmp_path: str, ini_cleaner: Callable) -> None:
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


@pytest.mark.unit_test
def test_write_with_custom_serializer(tmp_path: str, ini_cleaner: Callable) -> None:
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
