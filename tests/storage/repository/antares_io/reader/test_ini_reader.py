import textwrap
from pathlib import Path

import pytest

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.io.reader.ini_reader import (
    MultipleSameKeysIniReader,
)


@pytest.mark.unit_test
def test_read(tmp_path: Path) -> None:
    path = Path(tmp_path) / "test.ini"
    path.write_text(
        textwrap.dedent(
            """
            [part1]
            key_int = 1
            key_float = 2.1
            key_str = value1
        
            [part2]
            key_bool = True
            key_bool2 = False
            """
        )
    )

    reader = IniReader()
    actual = reader.read(path)

    expected = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    assert actual == expected

    with path.open() as f:
        actual_from_bytes = reader.read(f)
        assert actual_from_bytes == expected


def test_read_sets_init(tmp_path: Path) -> None:
    path = Path(tmp_path) / "test.ini"
    path.write_text(
        textwrap.dedent(
            """
            [part1]
            key_int = 1
            key_float = 2.1
            key_str = value1

            [part2]
            key_bool = true
            key_bool = false
            """
        )
    )

    reader = MultipleSameKeysIniReader()
    actual = reader.read(path)

    expected = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": [True, False]},
    }

    assert actual == expected

    with path.open() as f:
        actual_from_bytes = reader.read(f)
        assert actual_from_bytes == expected


def test_read__with_special_keys(tmp_path: Path) -> None:
    path = Path(tmp_path) / "test.ini"
    path.write_text(
        textwrap.dedent(
            """
            [chap]
            + = areaA
            + = areaB
            """
        )
    )

    reader = MultipleSameKeysIniReader(special_keys=["+"])
    actual = reader.read(path)

    expected = {
        "chap": {"+": ["areaA", "areaB"]},
    }

    assert actual == expected

    with path.open() as f:
        actual_from_bytes = reader.read(f)
        assert actual_from_bytes == expected
