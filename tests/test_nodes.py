from pathlib import Path
from unittest.mock import Mock

from api_iso_antares.engine.nodes import MixFolderNode, INode
from api_iso_antares.jsonschema import JsonSchema


def test_mix_folder_with_zones_list(project_path: Path) -> None:
    path = project_path / "tests/engine/resources/s1/areas"
    jsm = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "rte-metadata": {"strategy": "S1"},
        "properties": {
            "list": {
                "type": "string",
            },
            "sets": {
                "type": "string",
            },
        },
        "additionalProperties": {"type": "string"},
    }
    content = "Hello, World"
    expected = {
        "list": content,
        "sets": content,
        "fr": content,
        "de": content,
        "it": content,
        "es": content,
    }

    node = Mock()
    node.get_content.return_value = content
    factory = Mock()
    factory.build.return_value = node

    node = MixFolderNode(
        path=path,
        jsm=JsonSchema(jsm),
        ini_reader=Mock(),
        parent=None,
        node_factory=factory,
    )
    json = node.get_content()

    assert expected == json
