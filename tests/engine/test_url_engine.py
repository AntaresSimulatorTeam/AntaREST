from pathlib import Path

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine import UrlEngine
from api_iso_antares.jsm import JsonSchema
from tests.conftest import get_strategy

content = 42


@pytest.mark.unit_test
def test_default_strategy(lite_jsonschema: JSON, lite_path: Path):
    expected_sub_jsm = lite_jsonschema["properties"]["folder3"]
    expected_sub_path = lite_path / "folder3"
    jsm = JsonSchema(lite_jsonschema)

    sub_jsm, sub_path = UrlEngine.default_strategy(
        jsm=jsm, part="folder3", path=lite_path
    )

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path


@pytest.mark.unit_test
def test_output_strategy(project_path: Path):
    jsm, expected_json_data, path = get_strategy(project_path, "S12")

    expected_sub_jsm = jsm
    expected_sub_path = path

    url = "output/"

    sub_jsm, sub_path = UrlEngine.output_strategy(
        jsm=jsm, part="output", path=path
    )

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path


@pytest.mark.unit_test
def test_output_strategy_with_id(project_path: Path):
    jsm, expected_json_data, path = get_strategy(project_path, "S12")

    expected_sub_jsm = jsm.get_child()
    expected_sub_path = path / "20201009-1221eco-hello-world"

    sub_jsm, sub_path = UrlEngine.output_strategy(jsm=jsm, part="2", path=path)

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path


@pytest.mark.unit_test
def test_output_link_strategy(project_path: Path):
    jsm, expected_json_data, path = get_strategy(project_path, "S12")
    url = "es/fr"

    expected_sub_jsm = jsm.get_child()
    expected_sub_path = path / "es - fr"

    sub_jsm, sub_path = UrlEngine.output_links_strategy(
        jsm=jsm, part="es", path=path, url=url
    )

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path


@pytest.mark.unit_test
def test_resolve(lite_jsonschema: JSON, lite_path: Path):

    url = "folder1/file2"

    jsm = JsonSchema(lite_jsonschema)
    expected_sub_jsm = jsm.get_child("folder1").get_child("file2")

    expected_sub_path = lite_path / "folder1/file2.ini"

    engine = UrlEngine(jsm=jsm)
    sub_jsm, sub_path, keys = engine.resolve(url=url, path=lite_path)

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path
    assert keys == ""


@pytest.mark.unit_test
def test_resolve_in_ini(lite_jsonschema: JSON, lite_path: Path):

    url = "folder1/file2/section/params"

    jsm = JsonSchema(lite_jsonschema)
    expected_sub_jsm = (
        jsm.get_child("folder1")
        .get_child("file2")
        .get_child("section")
        .get_child("params")
    )

    expected_sub_path = lite_path / "folder1/file2.ini"

    engine = UrlEngine(jsm=jsm)
    sub_jsm, sub_path, keys = engine.resolve(url=url, path=lite_path)

    assert sub_jsm == expected_sub_jsm
    assert sub_path == expected_sub_path
    assert keys == "section/params"

