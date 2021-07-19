from pathlib import Path
from typing import Callable

import pytest

from antarest.storage.business.rawstudy.io.reader import IniReader
from antarest.storage.business.rawstudy.io.reader.ini_reader import (
    SetsIniReader,
)


@pytest.mark.unit_test
def test_read(tmp_path: str, clean_ini_writer: Callable) -> None:
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

    clean_ini_writer(path, ini_content)

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    reader = IniReader()
    assert reader.read(path) == expected_json


def test_read_sets_init(tmp_path: str, clean_ini_writer) -> None:
    path = Path(tmp_path) / "test.ini"

    ini_content = """
        [part1]
        key_int = 1
        key_float = 2.1
        key_str = value1
        
        [part2]
        key_bool = true
        key_bool = false
    """

    clean_ini_writer(path, ini_content)

    exp_data = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": [True, False]},
    }

    assert SetsIniReader().read(path) == exp_data
