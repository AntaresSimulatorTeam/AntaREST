from pathlib import Path

import pytest

from api_iso_antares.antares_io.ini import read_ini


@pytest.mark.unit_test
def test_read_ini(tmp_path: str) -> None:
    path = Path(tmp_path) / "test.ini"

    ini_content = """
    [part1]
    key_int = 1
    key_float = 2.1
    key_str = value1

    [part2]
    key_bool = true
    key_bool2 = false
    """

    path.write_text(ini_content)

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    assert read_ini(path) == expected_json
