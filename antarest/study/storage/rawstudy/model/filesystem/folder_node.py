import shutil
from abc import abstractmethod, ABC
from typing import List, Optional, Tuple, Union, Dict

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import (
    INode,
    TREE,
)


class FilterError(Exception):
    pass


class ChildNotFoundError(Exception):
    pass


class FolderNode(INode[JSON, Union[str, bytes, JSON], JSON], ABC):
    """
    Hub node which forward request deeper in tree according to url. Or expand request according to depth.
    Its children is set node by node following antares tree structure.
    Strucuture is implemented in antarest.study.repository.filesystem.root
    """

    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig
    ) -> None:
        self.config = config
        self.context = context

    @abstractmethod
    def build(self, config: FileStudyTreeConfig) -> TREE:
        pass

    def _forward_get(
        self,
        url: List[str],
        depth: int = -1,
        formatted: bool = True,
    ) -> JSON:
        children = self.build(self.config)
        names, sub_url = self.extract_child(children, url)

        # item is unique in url
        if len(names) == 1:
            return children[names[0]].get(  # type: ignore
                sub_url, depth=depth, expanded=False, formatted=formatted
            )
        # many items asked or * asked
        else:
            return {
                key: children[key].get(
                    sub_url, depth=depth, expanded=False, formatted=formatted
                )
                for key in names
            }

    def _expand_get(
        self,
        depth: int = -1,
        formatted: bool = True,
    ) -> JSON:
        children = self.build(self.config)

        if depth == 0:
            return {}
        return {
            name: node.get(depth=depth - 1, expanded=True, formatted=formatted)
            if depth - 1 != 0
            else {}
            for name, node in children.items()
        }

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        if url and url != [""]:
            return self._forward_get(url, depth, formatted)
        else:
            return self._expand_get(depth, formatted)

    def save(
        self, data: Union[str, bytes, JSON], url: Optional[List[str]] = None
    ) -> None:
        children = self.build(self.config)
        url = url or []

        if url:
            (name,), sub_url = self.extract_child(children, url)
            return children[name].save(data, sub_url)
        else:
            if not self.config.path.exists():
                self.config.path.mkdir()
            assert isinstance(data, Dict)
            for key in data:
                children[key].save(data[key])

    def delete(self, url: Optional[List[str]] = None) -> None:
        if url and url != [""]:
            children = self.build(self.config)
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
        children = self.build(self.config)

        if url and url != [""]:
            (name,), sub_url = self.extract_child(children, url)
            return children[name].check_errors(data, sub_url, raising)
        else:
            errors: List[str] = list()
            for key in data:
                if key not in children:
                    msg = f"key={key} not in {list(children.keys())} for {self.__class__.__name__}"
                    if raising:
                        raise ValueError(msg)
                    errors += [msg]
                else:
                    errors += children[key].check_errors(
                        data[key], raising=raising
                    )
            return errors

    def normalize(self) -> None:
        for child in self.build(self.config).values():
            child.normalize()

    def denormalize(self) -> None:
        for child in self.build(self.config).values():
            child.denormalize()

    def extract_child(
        self, children: TREE, url: List[str]
    ) -> Tuple[List[str], List[str]]:
        names, sub_url = url[0].split(","), url[1:]
        names = list(children.keys()) if names[0] == "*" else names
        if names[0] not in children:
            raise ChildNotFoundError(
                f"{names[0]} not a children of {self.__class__.__name__}"
            )
        child_class = type(children[names[0]])
        for name in names:
            if name not in children:
                raise ChildNotFoundError(
                    f"{name} not a children of {self.__class__.__name__}"
                )
            if type(children[name]) != child_class:
                raise FilterError("Filter selection has different classes")
        return names, sub_url
