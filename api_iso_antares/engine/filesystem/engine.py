from pathlib import Path
from typing import Any, cast, Dict

from api_iso_antares.antares_io.writer.ini_writer import IniWriter
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.filesystem.nodes import NodeFactory
from api_iso_antares.jsm import JsonSchema


class FileSystemEngine:
    def __init__(
        self,
        jsm: JsonSchema,
        readers: Dict[str, Any],
        writers: Dict[str, Any],
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

    def write(self, path: Path, data: JSON) -> None:
        path.mkdir()
        self.r_write(path, data, self.jsm)

    def r_write(self, path: Path, data: JSON, jsm: JsonSchema) -> None:
        if not data:
            return
        children = data.keys()

        for child in children:
            sub_jsm = self.get_jsm_child(child, jsm)
            if sub_jsm.is_file():
                filename = self.build_filepath(path, child, sub_jsm)
                filename.touch()
                if filename.suffix in [".ini", ".antares", ".dat"]:
                    IniWriter().write(data=data[child], path=filename)
            else:
                (path / child).mkdir()
                self.r_write(path / child, data[child], sub_jsm)

    @staticmethod
    def build_filepath(path: Path, file_stem: str, jsm: JsonSchema) -> Path:
        if jsm.get_filename():
            filename = Path("/".join([str(path), str(jsm.get_filename())]))
        else:
            filename = Path(
                "/".join(
                    [
                        str(path),
                        file_stem + str(jsm.get_metadata_element("file_ext")),
                    ]
                )
            )
        return filename

    @staticmethod
    def get_jsm_child(child: str, jsm: "JsonSchema") -> "JsonSchema":
        if (
            jsm.has_additional_properties()
            and child not in jsm.get_properties()
        ):
            return jsm.get_additional_properties()
        return jsm.get_child(child)

    def get_reader(self, reader: str = "default") -> Any:
        return self.node_factory.readers[reader]

    def get_writer(self, reader: str = "default") -> Any:
        return self.writers[reader]
