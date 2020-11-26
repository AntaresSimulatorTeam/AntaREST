import abc
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from api_iso_antares.antares_io.reader import IniReader, SetsIniReader
from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.jsm import JsonSchema


class INode(abc.ABC):
    def __init__(
        self,
        deep_path: Path,
        jsm: JsonSchema,
        ini_reader: IniReader,
        node_factory: "NodeFactory",
        study_path: Optional[Path] = None,
    ) -> None:
        self._deep_path = deep_path
        self.study_path = study_path or deep_path
        self._jsm = jsm
        self._ini_reader = ini_reader
        self._node_factory = node_factory

    def get_filename(self) -> str:
        return self._deep_path.name

    def get_content(self) -> SUB_JSON:
        return self._build_content()

    def parse_properties(
        self, not_checking: bool = False
    ) -> Tuple[Dict[str, "INode"], List[str]]:
        output: Dict[str, "INode"] = dict()
        properties = self._jsm.get_properties()

        filenames: List[str] = []

        for key in properties:
            file = self._deep_path / (
                self._jsm.get_child(key).get_filename() or key
            )

            # TODO: try to refacto not_cheking (remove ?)
            if not_checking or file.exists():
                child_node = self._node_factory.build(
                    key=key,
                    deep_path=self._deep_path,
                    study_path=self.study_path,
                    jsm=self._jsm.get_child(key),
                )
                output[key] = child_node
                filenames.append(child_node.get_filename())

        return output, filenames

    def parse_additional_properties(
        self, avoid_filenames: Optional[List[str]] = None
    ) -> Dict[Path, "INode"]:
        avoid_filenames = avoid_filenames or list()
        children: Dict[Path, "INode"] = dict()
        for folder in self._deep_path.iterdir():
            if folder.name not in avoid_filenames:
                children[folder] = self._node_factory.build(
                    key=folder.name,
                    deep_path=self._deep_path,
                    study_path=self.study_path,
                    jsm=self._jsm.get_additional_properties(),
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
            output[path.stem] = child.get_content()

        return output


class IniFileNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._deep_path
        return self._ini_reader.read(path)


class SetsIniFileNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._deep_path
        return SetsIniReader.read(path)


class UrlFileNode(INode):
    def _build_content(self) -> SUB_JSON:
        path = self._deep_path
        parts = path.parts
        # remove all path before study folder
        root = len(self.study_path.parts) - 1
        relative_path = "/".join(parts[root:])
        return f"file/{relative_path}"


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
            "mode": modes[regex.group(2)],
            "name": regex.group(3),
        }

    def _build_content(self) -> SUB_JSON:
        output = dict()
        jsm = self._jsm.get_additional_properties()

        directories = self._get_child_directories()
        for i, directory in enumerate(directories):
            index = str(i + 1)
            output[index] = OutputFolderNode._parse_output(directory.name)
            for child in directory.iterdir():
                if (
                    child.stem in jsm.get_properties()
                ):  # TODO remove when jsonschema fully made
                    output[index][child.stem] = self._node_factory.build(
                        key=child.name,
                        deep_path=directory,
                        study_path=self.study_path,
                        jsm=jsm.get_child(child.stem),
                    ).get_content()
        return output

    def _get_child_directories(self) -> List[Path]:
        pattern = self._jsm.get_pattern_properties()
        if pattern is not None:
            directories = filter(
                lambda path: re.match(pattern, path.name),
                self._deep_path.iterdir(),
            )
        else:
            directories = self._deep_path.iterdir()
        return sorted(directories)


class OutputLinksNode(INode):
    @staticmethod
    def _parse_folder_name(path: Path) -> List[str]:
        return path.name.split(" - ")

    def _build_content(self) -> SUB_JSON:
        output: JSON = dict()

        for folder in self._deep_path.iterdir():
            src, dest = folder.name.split(" - ")
            if src not in output:
                output[src] = dict()

            jsm_link_one = self._jsm.get_additional_properties()
            jsm_link_two = jsm_link_one.get_additional_properties()

            output[src][dest] = self._node_factory.build(
                key=folder.name,
                deep_path=self._deep_path,
                study_path=self.study_path,
                jsm=jsm_link_two,
            ).get_content()

        return output


class InputLinksNode(INode):
    def _build_content(self) -> SUB_JSON:
        children: JSON = dict()
        for area in self._deep_path.iterdir():
            children[area.name] = MixFolderNode(
                area,
                study_path=self.study_path,
                jsm=self._jsm.get_additional_properties(),
                ini_reader=self._ini_reader,
                node_factory=self._node_factory,
            ).get_content()

        return children


class NodeFactory:
    def __init__(self, readers: Dict[str, Any]) -> None:
        self.readers = readers

    def build(
        self,
        key: str,
        deep_path: Path,
        jsm: JsonSchema,
        study_path: Optional[Path] = None,
    ) -> INode:
        study_path = study_path or deep_path
        deep_path = NodeFactory._build_path(deep_path, jsm, key)
        node_class = NodeFactory.get_node_class_by_strategy(jsm, deep_path)
        reader = self.get_reader("default")
        return node_class(deep_path, jsm, reader, self, study_path)

    def get_reader(self, key: str) -> Any:
        return self.readers[key]

    @staticmethod
    def get_node_class_by_strategy(jsm: JsonSchema, path: Path) -> Type[INode]:

        node_class: Type[INode] = ObjectNode
        strategy = jsm.get_strategy()

        if strategy in ["S1", "S3"]:
            return MixFolderNode
        elif strategy in ["S2", "S16"]:
            return IniFileNode
        elif strategy in ["S4", "S6", "S9", "S10", "S7"]:
            return OnlyListNode
        elif strategy in ["S12"]:
            return OutputFolderNode
        elif strategy in ["S13"]:
            return SetsIniFileNode
        elif strategy in ["S14"]:
            return InputLinksNode
        elif strategy in ["S15"]:
            return OutputLinksNode

        if path.is_file():
            if path.suffix in [".txt", ".log", ".ico"]:
                node_class = UrlFileNode
            elif path.suffix in [".ini", ".antares", ".dat"]:
                node_class = IniFileNode
        else:
            if jsm.is_object():
                node_class = ObjectNode
        return node_class

    @staticmethod
    def _build_path(path: Path, jsm: JsonSchema, key: str) -> Path:
        if path.is_file():
            return path
        file_or_directory_name: Optional[str] = jsm.get_filename()
        if file_or_directory_name is None:
            file_or_directory_name = key
        return path / file_or_directory_name
