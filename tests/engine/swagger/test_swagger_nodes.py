from unittest.mock import Mock

from api_iso_antares.engine.swagger.nodes import PathNode, RootNode


def test_path_node() -> None:

    parent = Mock()
    parent.get_url.return_value = "/ex1/ex2"

    node = PathNode(
        key="ex3",
        jsm=Mock(),
        node_factory=Mock(),
        parent=parent,
    )

    assert node.get_url() == "/ex1/ex2/ex3"

    data_path = node.get_path().json()
    assert data_path["get"]["tags"] == ["ex3"]


def test_root_node() -> None:

    jsm = Mock()
    jsm.get_properties.return_value = []

    root = RootNode(jsm=jsm)

    assert root.get_url() == "/metadata/{study}"

    root.build_content()

    data = root.get_content()
    assert data["openapi"] == "3.0.0"
    assert data["paths"]["/metadata/{study}"]["get"]["responses"] is not None
