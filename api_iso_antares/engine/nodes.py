import abc
from pathlib import Path
from typing import Any, cast, Dict, List, Optional, Type

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.jsonschema import JsonSchema


class INode(abc.ABC):
    def __init__(
        self,
        path: Path,
        jsm: JsonSchema,
        ini_reader: IniReader,
        parent: Optional["INode"],
        node_factory: "NodeFactory",
    ) -> None:
        self._path = path
        self._jsm = jsm
        self._ini_reader = ini_reader
        self._parent = parent
        self._node_factory = node_factory

    def get_filename(self) -> str:
        return self._path.name

    def get_content(self) -> SUB_JSON:
        return self._build_content()

    def get_root_path(self) -> Path:
        if self._parent is None:
            return self._path
        return self._parent.get_root_path()

    @abc.abstractmethod
    def _build_content(self) -> SUB_JSON:
        pass


class ObjectNode(INode):
    def _build_content(self) -> SUB_JSON:

        output: Dict[str, SUB_JSON] = dict()

        for key in self._jsm.get_properties():

            child_node = self._node_factory.build(
                key=key,
                root_path=self._path,
                jsm=self._jsm.get_child(key),
                parent=self,
            )

            output[key] = child_node.get_content()

        return output


class MixFolderNode(INode):
    def _build_content(self) -> SUB_JSON:
        output: JSON = dict()
        properties = self._jsm.get_properties()

        filenames: List[str] = []

        for key in properties:
            child_node = self._node_factory.build(
                key=key,
                root_path=self._path,
                jsm=self._jsm.get_child(key),
                parent=self,
            )
            output[key] = child_node.get_content()
            filenames.append(child_node.get_filename())

        for folder in self._path.iterdir():
            if folder.name not in filenames:
                key = folder.name
                # TODO '*' to refactor
                child_node = self._node_factory.build(
                    key=key,
                    root_path=self._path,
                    jsm=self._jsm.get_additional_properties(),
                    parent=self,
                )
                output[key] = child_node.get_content()

        return output


class ArrayNode(INode):
    def _build_content(self) -> SUB_JSON:

        output: List[SUB_JSON] = list()

        for key in self._get_children():

            child_node = self._node_factory.build(
                key=key,
                root_path=self._path,
                jsm=self._jsm.get_child(),
                parent=self,
            )

            # TODO: True now... False later. A child of an array node will not always be a Dict

            child_content: JSON = cast(JSON, child_node.get_content())
            child_content["$id"] = key
            output.append(child_content)

        return output

    def _get_children(self) -> List[str]:
        return [path.name for path in sorted(self._path.iterdir())]


class IniFileNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._path
        return self._ini_reader.read(path)


class UrlFileNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._path
        relative_path = str(path).replace(str(self.get_root_path().parent), "")
        return f"file{relative_path}"


class OnlyListNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._path

        output = {}
        for file in path.iterdir():
            key = file.stem
            child_node = self._node_factory.build(
                key=file.name,
                root_path=path,
                jsm=self._jsm.get_additional_properties(),
                parent=self,
            )

            output[key] = child_node.get_content()

        return output


class NodeFactory:
    def __init__(self, readers: Dict[str, Any]) -> None:
        self.readers = readers

    def build(
        self,
        key: str,
        root_path: Path,
        jsm: JsonSchema,
        parent: Optional[INode] = None,
    ) -> INode:
        path = NodeFactory._build_path(root_path, jsm, key)
        node_class = NodeFactory.get_node_class_by_strategy(jsm, path)
        reader = self.get_reader("default")
        return node_class(path, jsm, reader, parent, self)

    def get_reader(self, key: str) -> Any:
        return self.readers[key]

    @staticmethod
    def get_node_class_by_strategy(jsm: JsonSchema, path: Path) -> Type[INode]:

        node_class: Type[INode] = ObjectNode
        strategy = jsm.get_strategy()
        if strategy in ["S1", "S3", "S7"]:
            return MixFolderNode
        elif strategy in ["S2"]:
            return IniFileNode
        elif strategy in ["S4", "S6"]:
            return OnlyListNode

        if path.is_file():
            if path.suffix in [".txt", ".log"]:
                node_class = UrlFileNode
            elif path.suffix in [
                ".ini",
                ".antares",
            ]:
                node_class = IniFileNode
        else:
            if jsm.is_array():
                node_class = ArrayNode
            elif jsm.is_object():
                node_class = ObjectNode

        return node_class

    @staticmethod
    def _build_path(path: Path, jsm: JsonSchema, key: str) -> Path:
        file_or_directory_name: Optional[str] = jsm.get_filename()
        if file_or_directory_name is None:
            file_or_directory_name = key
        return path / file_or_directory_name
