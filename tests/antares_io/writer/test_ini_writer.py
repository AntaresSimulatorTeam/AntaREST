from pathlib import Path
from typing import Callable

import pytest

from api_iso_antares.antares_io.writer.ini_writer import IniWriter


@pytest.mark.unit_test
def test_write(tmp_path: str, ini_cleaner: Callable) -> None:
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

    json_data = {
        "part1": {"key_int": 1, "key_float": 2.1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    writer = IniWriter()
    writer.write(json_data, path)

    assert ini_cleaner(ini_content) == ini_cleaner(path.read_text())
