from pathlib import Path

from api_iso_antares.antares_io.ini import read_ini


def test_read_ini(tmp_path: str) -> None:
    path = Path(tmp_path) / "test.ini"

    ini_content = """
    [part1]
    key_int = 1
    key_str = value1

    [part2]
    key_bool = true
    key_bool2 = false
    """

    path.write_text(ini_content)

    expected_dict = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }

    config = read_ini(path)
    assert config["part1"]["key_int"] == "1"
    assert config["part1"]["key_str"] == "value1"
    assert config["part2"]["key_bool"] == "true"
    assert config["part2"]["key_bool2"] == "false"
    assert config["part2"].getboolean("key_bool") is True
