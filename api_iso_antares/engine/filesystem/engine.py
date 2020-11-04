from pathlib import Path
from typing import Any, cast, Dict

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.filesystem.nodes import NodeFactory
from api_iso_antares.jsm import JsonSchema


class FileSystemEngine:
    def __init__(
        self,
        jsm: JsonSchema,
        readers: Dict[str, Any],
        writers: Dict[str, Any] = {},
    ) -> None:
        self.jsm = jsm
        self.node_factory = NodeFactory(readers=readers)
        self.writers = writers

    def parse(self, path: Path) -> JSON:
        root_node = self.node_factory.build(
            key="",
            root_path=path,
            jsm=self.jsm,
        )
        return cast(JSON, root_node.get_content())

    def get_reader(self, reader: str = "default") -> Any:
        return self.node_factory.readers[reader]

    def get_writer(self, reader: str = "default") -> Any:
        return self.writers[reader]
