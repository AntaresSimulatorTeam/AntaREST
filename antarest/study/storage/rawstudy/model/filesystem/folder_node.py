import shutil
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Dict, List, Optional, Tuple, Union

from fastapi import HTTPException

from antarest.core.model import JSON, SUB_JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode


class FilterError(Exception):
    pass


class ChildNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class FolderNode(INode[JSON, SUB_JSON, JSON], ABC):
    # noinspection SpellCheckingInspection
    """
    A node in the Antares tree structure that represents a folder in a filesystem.

    This class is responsible for forwarding requests deeper in the tree according
    to the provided URL, or expanding requests according to the depth of the folder
    structure. It is a hub node that can have child nodes added to it as required
    to build out the tree.

    The Antares tree structure is implemented in the
    `antarest.study.storage.rawstudy.model.filesystem` module.
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        children_glob_exceptions: Optional[List[str]] = None,
    ) -> None:
        super().__init__(config)
        self.context = context
        self.children_glob_exceptions = children_glob_exceptions or []

    @abstractmethod
    def build(self) -> TREE:
        pass

    def _forward_get(
        self,
        url: List[str],
        depth: int = -1,
        formatted: bool = True,
        get_node: bool = False,
    ) -> Union[JSON, INode[JSON, SUB_JSON, JSON]]:
        children = self.build()
        names, sub_url = self.extract_child(children, url)

        # item is unique in url
        if len(names) == 1:
            child = children[names[0]]
            if not get_node:
                return child.get(sub_url, depth=depth, expanded=False, formatted=formatted)  # type: ignore
            else:
                return child.get_node(
                    sub_url,
                )
        # many items asked or * asked
        else:
            if not get_node:
                return {
                    key: children[key].get(
                        sub_url,
                        depth=depth,
                        expanded=False,
                        formatted=formatted,
                    )
                    for key in names
                }
            else:
                raise ValueError("Multiple nodes requested")

    def _expand_get(
        self, depth: int = -1, formatted: bool = True, get_node: bool = False
    ) -> Union[JSON, INode[JSON, SUB_JSON, JSON]]:
        if get_node:
            return self

        children = self.build()

        if depth == 0:
            return {}
        return {
            name: node.get(depth=depth - 1, expanded=True, formatted=formatted) if depth != 1 else {}
            for name, node in children.items()
        }

    def _get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        formatted: bool = True,
        get_node: bool = False,
    ) -> Union[JSON, INode[JSON, SUB_JSON, JSON]]:
        if url and url != [""]:
            return self._forward_get(url, depth, formatted, get_node)
        else:
            return self._expand_get(depth, formatted, get_node)

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        output = self._get(url=url, depth=depth, formatted=formatted, get_node=False)
        assert not isinstance(output, INode)
        return output

    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[JSON, SUB_JSON, JSON]:
        output = self._get(url=url, get_node=True)
        assert isinstance(output, INode)
        return output

    def save(
        self,
        data: SUB_JSON,
        url: Optional[List[str]] = None,
    ) -> None:
        self._assert_not_in_zipped_file()
        children = self.build()
        if not self.config.path.exists():
            self.config.path.mkdir()

        if url := url or []:
            (name,), sub_url = self.extract_child(children, url)
            return children[name].save(data, sub_url)
        else:
            assert isinstance(data, dict)
            for key in data:
                children[key].save(data[key])

    def delete(self, url: Optional[List[str]] = None) -> None:
        if url and url != [""]:
            children = self.build()
            names, sub_url = self.extract_child(children, url)
            for key in names:
                children[key].delete(sub_url)
        elif self.config.path.exists():
            shutil.rmtree(self.config.path)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        children = self.build()

        if url and url != [""]:
            (name,), sub_url = self.extract_child(children, url)
            return children[name].check_errors(data, sub_url, raising)
        else:
            errors: List[str] = []
            for key in data:
                if key not in children:
                    msg = f"key={key} not in {list(children.keys())} for {self.__class__.__name__}"
                    if raising:
                        raise ValueError(msg)
                    errors += [msg]
                else:
                    errors += children[key].check_errors(data[key], raising=raising)
            return errors

    def normalize(self) -> None:
        for child in self.build().values():
            child.normalize()

    def denormalize(self) -> None:
        for child in self.build().values():
            child.denormalize()

    def extract_child(self, children: TREE, url: List[str]) -> Tuple[List[str], List[str]]:
        names, sub_url = url[0].split(","), url[1:]
        names = (
            list(
                filter(
                    lambda c: c not in self.children_glob_exceptions,
                    children.keys(),
                )
            )
            if names[0] == "*"
            else names
        )

        if len(names) == 0:
            return [], sub_url

        if names[0] not in children:
            raise ChildNotFoundError(f"'{names[0]}' not a child of {self.__class__.__name__}")
        child_class = type(children[names[0]])
        for name in names:
            if name not in children:
                raise ChildNotFoundError(f"'{name}' not a child of {self.__class__.__name__}")
            if type(children[name]) != child_class:
                raise FilterError("Filter selection has different classes")
        return names, sub_url
