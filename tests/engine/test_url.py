from typing import Dict, Any

from api_iso_antares.engine.url import UrlEngine
from api_iso_antares.types import JSON


def test_get_right_settings(
    test_jsonschema: JSON, test_json_data: JSON
) -> None:
    path = "part1/key_int"
    url_engine = UrlEngine(test_jsonschema, test_json_data)

    assert url_engine.apply(path) == 1


def test_get_wrong_path(test_jsonschema: JSON, test_json_data: JSON) -> None:
    path = "WRONG/PATH"
    url_engine = UrlEngine(test_jsonschema, test_json_data)

    assert url_engine.apply(path) is None
