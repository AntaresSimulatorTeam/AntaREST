import pytest

from api_iso_antares.engine import UrlEngine
from api_iso_antares.custom_types import JSON


@pytest.mark.unit_test
def test_get_right_settings(test_json_data: JSON) -> None:
    path = "part1/key_int"
    url_engine = UrlEngine(jsonschema={})

    assert url_engine.apply(path, test_json_data) == 1


@pytest.mark.unit_test
def test_get_wrong_path(test_json_data: JSON) -> None:
    path = "WRONG/PATH"
    url_engine = UrlEngine(jsonschema={})

    assert url_engine.apply(path, test_json_data) is None
