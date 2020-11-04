from unittest.mock import Mock

import pytest

from api_iso_antares.engine.swagger.nodes import (
    PathNode,
    RootNode,
)
from api_iso_antares.jsm import JsonSchema


@pytest.mark.unit_test
def test_path_node() -> None:

    parent = Mock()
    parent.get_url.return_value = "/ex1/ex2"

    jsm = Mock()
    jsm.has_properties.return_value = False
    jsm.has_defined_additional_properties.return_value = False

    node = PathNode(
        key="ex3",
        jsm=jsm,
        node_factory=Mock(),
        parent=parent,
    )

    assert node.get_url() == "/ex1/ex2/ex3"

    data_path = node._get_path().json()
    assert data_path["get"]["tags"] == ["ex3"]


@pytest.mark.unit_test
def test_root_node() -> None:

    jsm = Mock()
    jsm.get_properties.return_value = []

    root = RootNode(jsm=jsm)

    assert root.get_url() == "/metadata/{study}"

    data = root.get_content()
    assert data["openapi"] == "3.0.0"
    assert data["paths"]["/metadata/{study}"]["get"]["responses"] is not None


@pytest.mark.unit_test
def test_array_node() -> None:

    jsm = {
        "type": "object",
        "properties": {
            "key_array": {"type": "array", "items": {"type": "string"}}
        },
    }

    root_node = RootNode(jsm=JsonSchema(jsm))

    print(root_node.get_content()["paths"])

    paths = root_node.get_content()["paths"]

    assert "/metadata/{study}/key_array" in paths.keys()
