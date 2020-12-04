from pathlib import Path

import pytest

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_node import IniNode


@pytest.mark.unit_test
def test_read(tmp_path: str) -> None:
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

    expected_json = {
        "part1": {"key_int": 1, "key_str": "value1", "key_float": 2.1},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    node = IniNode(Config(path), types=types)
    assert node.get([]) == expected_json
    assert node.get(["part2"]) == {"key_bool": True, "key_bool2": False}
    assert node.get(["part2", "key_bool"])
