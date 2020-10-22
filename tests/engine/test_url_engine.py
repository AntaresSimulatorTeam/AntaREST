from pathlib import Path

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.url_engine import UrlNotMatchJsonDataError


@pytest.mark.unit_test
def test_get_right_settings(test_json_data: JSON) -> None:
    path = Path("part1/key_int")
    url_engine = UrlEngine(jsm={})

    assert url_engine.apply(path, test_json_data) == 1


@pytest.mark.unit_test
def test_get_wrong_path(test_json_data: JSON) -> None:
    path = Path("WRONG/PATH")
    url_engine = UrlEngine(jsm={})

    with pytest.raises(UrlNotMatchJsonDataError):
        url_engine.apply(path, test_json_data, depth=-1)


@pytest.mark.unit_test
def test_get_right_settings_with_depth() -> None:
    data = {
        "level0": {
            "value1": 43,
            "level1": {
                "value2": 3.14,
                "level2": {
                    "value3": True,
                    "level3": {"value4": "hello, world", "level4": {}},
                },
            },
        }
    }

    url_engine = UrlEngine(jsm={})

    expected_enough_depth = {
        "value1": 43,
        "level1": {"value2": 3.14, "level2": None},
    }
    assert url_engine.apply(Path("level0/"), data, 2) == expected_enough_depth

    expected_not_enough_depth = data["level0"]
    assert (
        url_engine.apply(Path("level0/"), data, 10)
        == expected_not_enough_depth
    )

    expected_deeper_depth = {"value4": "hello, world", "level4": None}
    assert (
        url_engine.apply(Path("level0/level1/level2/level3"), data, 1)
        == expected_deeper_depth
    )


@pytest.mark.unit_test
def test_get_array_items(lite_jsondata: JSON) -> None:
    data = lite_jsondata

    url_engine = UrlEngine(jsm={})

    expected = str(Path("file/root1/folder3/areas/area1/matrice1.txt"))

    assert (
        url_engine.apply(Path("folder3/areas/area1/matrice1.txt"), data)
        == expected
    )
