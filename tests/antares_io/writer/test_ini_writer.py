from pathlib import Path

import pytest

from api_iso_antares.antares_io.writer.ini_writer import IniWriter


def remove_white_space(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.unit_test
def test_write(tmp_path: str) -> None:
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

    assert remove_white_space(ini_content) == remove_white_space(
        path.read_text()
    )
