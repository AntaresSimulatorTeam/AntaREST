from pathlib import Path
from typing import Any, cast, Dict, Iterator

from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.engine.filesystem.nodes import NodeFactory
from api_iso_antares.jsm import JsonSchema


class FileSystemElement:
    def __init__(self, path: Path, data: SUB_JSON, jsm: JsonSchema):
        self._path = path
        self._data = data
        self._jsm = jsm

    def get_path(self) -> Path:
        return self._path

    def get_data(self) -> SUB_JSON:
        return self._data

    def get_jsm(self) -> JsonSchema:
        return self._jsm

    def is_file(self) -> bool:
        return self.get_jsm().is_file()

    def mkdir(self) -> None:
        if not self._path.exists():
            self._path.mkdir()

    def is_ini_file(self) -> bool:
        return self.get_path().suffix in [".ini", ".antares", ".dat"]

    def is_matrix_url(self) -> bool:
        url = cast(str, self.get_data())
        return url.startswith("file/")

    def get_children(self) -> Iterator["FileSystemElement"]:

        if self.has_children():
            sub_items = cast(Dict[str, SUB_JSON], self.get_data())
            for sub_name, sub_data in sub_items.items():
                sub_jsm = self.get_jsm().get_child(key=sub_name)
                sub_path = self._build_filepath(sub_name, sub_jsm)
                yield FileSystemElement(
                    path=sub_path, data=sub_data, jsm=sub_jsm
                )

    def has_children(self) -> bool:
        return self.is_dir() and isinstance(self.get_data(), dict)

    def is_dir(self) -> bool:
        return self.get_path().is_dir()

    def _build_filepath(self, child_name: str, child_jsm: JsonSchema) -> Path:

        filename = child_jsm.get_filename() or child_name
        extension = child_jsm.get_filename_extension() or ""

        return self.get_path() / (filename + extension)


class FileSystemEngine:
    def __init__(
        self,
        jsm: JsonSchema,
        readers: Dict[str, Any],
        writers: Dict[str, Any],
    ) -> None:
        self.jsm = jsm
        self.node_factory = NodeFactory(readers=readers)
        self.writer = FileSystemWriter(writers)

    def get_reader(self, reader: str = "default") -> Any:
        return self.node_factory.readers[reader]

    def parse(self, path: Path) -> JSON:
        root_node = self.node_factory.build(
            key="",
            root_path=path,
            jsm=self.jsm,
        )
        return cast(JSON, root_node.get_content())

    def write(self, path: Path, data: JSON) -> None:
        element = FileSystemElement(path, data, self.jsm)
        self.writer.write(element, root_path=path)


class FileSystemWriter:
    def __init__(self, writers: Dict[str, Any]) -> None:
        self.writers = writers

    def get_writer(self, writer: str = "default") -> Any:
        return self.writers[writer]

    def write(self, element: FileSystemElement, root_path: Path) -> None:
        self.write_element(element, root_path)

        children = element.get_children()

        for child in children:
            self.write(child, root_path)

    def write_element(
        self, element: FileSystemElement, root_path: Path
    ) -> None:
        if element.is_file():
            self.write_file(element, root_path)
        else:
            element.mkdir()

    def write_file(self, element: FileSystemElement, root_path: Path) -> None:
        if element.is_ini_file():
            self.get_writer().write(
                data=element.get_data(), path=element.get_path()
            )
        elif element.is_matrix_url():
            url = cast(str, element.get_data())
            matrix_path = FileSystemWriter.url_in_filepath(
                url=url, root_path=root_path
            )
            self.get_writer("matrix").write(matrix_path, element.get_path())
        else:
            raise NotImplementedError(
                "A writer for this file is not implemented: "
                + str(element.get_path())
                + "with data: "
                + str(element.get_data())
            )

    @staticmethod
    def url_in_filepath(url: str, root_path: Path) -> Path:
        filesystem_parts = url.split("/")[1:]
        filepath = Path(root_path.parent)
        for part in filesystem_parts:
            filepath /= part
        return filepath
