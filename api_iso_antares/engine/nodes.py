import abc
import re
from pathlib import Path
from typing import Any, cast, Dict, List, Optional, Type, Tuple

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

    def parse_properties(
        self, not_checking: bool = False
    ) -> Tuple[Dict[str, "INode"], List[str]]:
        output: Dict[str, "INode"] = dict()
        properties = self._jsm.get_properties()

        filenames: List[str] = []

        for key in properties:
            file = self._path / (
                self._jsm.get_child(key).get_filename() or key
            )
            if not_checking or file.exists():
                child_node = self._node_factory.build(
                    key=key,
                    root_path=self._path,
                    jsm=self._jsm.get_child(key),
                    parent=self,
                )
                output[key] = child_node
                filenames.append(child_node.get_filename())

        return output, filenames

    def parse_additional_properties(
        self, avoid_filenames: Optional[List[str]] = None
    ) -> Dict[Path, "INode"]:
        avoid_filenames = avoid_filenames or list()
        children: Dict[Path, "INode"] = dict()
        for folder in self._path.iterdir():
            if folder.name not in avoid_filenames:
                children[folder] = self._node_factory.build(
                    key=folder.name,
                    root_path=self._path,
                    jsm=self._jsm.get_additional_properties(),
                    parent=self,
                )
        return children

    @abc.abstractmethod
    def _build_content(self) -> SUB_JSON:
        pass


class ObjectNode(INode):
    def _build_content(self) -> SUB_JSON:
        children, _ = self.parse_properties()
        return {key: child.get_content() for key, child in children.items()}


class MixFolderNode(INode):
    def _build_content(self) -> SUB_JSON:
        children, filenames = self.parse_properties(not_checking=True)
        output = {key: child.get_content() for key, child in children.items()}

        for path, child in self.parse_additional_properties(filenames).items():
            output[path.name] = child.get_content()

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
        children = self.parse_additional_properties().items()
        return {file.stem: child.get_content() for file, child in children}


class OutputFolderNode(INode):
    @staticmethod
    def _parse_output(name: str) -> JSON:
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search("^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", name)
        return {
            "date": regex.group(1),
            "type": modes[regex.group(2)],
            "name": regex.group(3),
        }

    def _build_content(self) -> SUB_JSON:
        output = dict()
        jsm = self._jsm.get_additional_properties()

        directories = sorted(self._path.iterdir())
        for i, dir in enumerate(directories):
            index = str(i + 1)
            output[index] = OutputFolderNode._parse_output(dir.name)
            for child in dir.iterdir():
                if (
                    child.stem in jsm.get_properties()
                ):  # TODO remove when jsonschema complet
                    output[index][child.stem] = self._node_factory.build(
                        key=child.name,
                        root_path=dir,
                        jsm=jsm.get_child(child.stem),
                        parent=self,
                    ).get_content()
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
        elif strategy in ["S4", "S6", "S9", "S10"]:
            return OnlyListNode
        elif strategy in ["S8"]:
            return OutputFolderNode

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
