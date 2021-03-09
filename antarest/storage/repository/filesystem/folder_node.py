from abc import abstractmethod, ABC
from typing import List, Optional, Tuple

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE


class FilterError(Exception):
    pass


class ChildNotFoundError(Exception):
    pass


class FolderNode(INode[JSON, JSON, JSON], ABC):
    def __init__(self, config: StudyConfig) -> None:
        self.config = config

    @abstractmethod
    def build(self, config: StudyConfig) -> TREE:
        pass

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        children = self.build(self.config)

        if url and url != [""]:
            names, sub_url = self.extract_child(children, url)
            if len(names) == 1:
                return children[names[0]].get(  # type: ignore
                    sub_url, depth=depth
                )
            else:
                return {
                    key: children[key].get(sub_url, depth=depth)
                    for key in names
                }

        else:
            if depth == 0:
                return {}
            json = {
                name: node.get(depth=depth - 1) if depth - 1 != 0 else {}
                for name, node in children.items()
            }
            return json

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        children = self.build(self.config)
        url = url or []

        if url:
            (name,), sub_url = self.extract_child(children, url)
            return children[name].save(data, sub_url)
        else:
            if not self.config.path.exists():
                self.config.path.mkdir()
            for key in data:
                children[key].save(data[key])

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

    def extract_child(
        self, children: TREE, url: List[str]
    ) -> Tuple[List[str], List[str]]:
        names, sub_url = url[0].split(","), url[1:]
        names = list(children.keys()) if names[0] == "*" else names
        child_class = type(children[names[0]])
        for name in names:
            if name not in children:
                raise ChildNotFoundError(
                    f"{name} not a children of {self.__class__.__name__}"
                )
            if type(children[name]) != child_class:
                raise FilterError("Filter selection has different classes")
        return names, sub_url
