from pathlib import Path
from typing import Callable

import pytest

from antarest.study.storage.rawstudy.io.writer.ini_writer import (
    IniWriter,
)


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
        key3 = [1,2,3]
    """

    json_data = {
        "part": {"key_int": 1, "key_float": 2.1, "key_str": "value1"},
        "partWithCapitals": {
            "key_bool": True,
            "key_bool2": False,
            "keyWithCapital": True,
        },
        "partWithSameKey": {
            "key": '["value1", "value2", "value3"]',
            "key2": '["4,2","1,3"]',
            "key3": "[1,2,3]",
        },
    }
    writer = IniWriter(special_keys=["key", "key2"])
    writer.write(json_data, path)

    assert ini_cleaner(ini_content) == ini_cleaner(path.read_text())
