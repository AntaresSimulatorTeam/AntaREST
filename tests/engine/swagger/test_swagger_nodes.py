from unittest.mock import Mock

import pytest

from api_iso_antares.engine.swagger.nodes import (
    PathNode,
    RootNode,
)
from api_iso_antares.jsm import JsonSchema


@pytest.mark.unit_test
def test_path_node() -> None:

    jsm = Mock()
    jsm.has_properties.return_value = False
    jsm.has_defined_additional_properties.return_value = False

    node = PathNode(
        url="/ex1/ex2/ex3",
        jsm=jsm,
        swagger=Mock(),
    )

    data_path = node._get_swagger_path().json()
    assert data_path["get"]["tags"] == ["ex3"]


@pytest.mark.unit_test
def test_root_node() -> None:

    jsm = Mock()
    jsm.get_properties.return_value = []

    root = RootNode(jsm=jsm)

    assert root.url == "/studies/{uuid}"

    data = root.get_content()
    assert data["openapi"] == "3.0.0"
    assert data["paths"]["/studies/{uuid}"]["get"]["responses"] is not None


@pytest.mark.unit_test
def test_array_node() -> None:

    jsm = {
        "type": "object",
        "properties": {
            "key_array": {"type": "array", "items": {"type": "string"}}
        },
    }

    root_node = RootNode(jsm=JsonSchema(jsm))

    paths = root_node.get_content()["paths"]

    assert "/studies/{uuid}/key_array" in paths.keys()


@pytest.mark.unit_test
def test_keyword_swagger_cut() -> None:

    jsm = {
        "type": "object",
        "properties": {
            "key1": {
                "rte-metadata": {"swagger_stop": True},
                "type": "object",
                "properties": {"key2": {"type": "string"}},
            }
        },
    }

    root_node = RootNode(jsm=JsonSchema(jsm))

    paths = root_node.get_content()["paths"]

    assert "/studies/{uuid}/key1" in paths.keys()
    assert "/studies/{uuid}/key1/key2" not in paths.keys()
