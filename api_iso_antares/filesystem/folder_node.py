from typing import List, Optional, Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.inode import INode, TREE


class FilterError(Exception):
    pass


class ChildNotFoundError(Exception):
    pass


class FolderNode(INode[JSON]):
    def __init__(self, config: Config, children: TREE) -> None:
        self.children: TREE = children
        self.config = config

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        if url and url != [""]:
            names, sub_url = self.extract_child(url)
            if len(names) == 1:
                return self.children[names[0]].get(sub_url, depth=depth)
            else:
                return {
                    key: self.children[key].get(sub_url, depth=depth)
                    for key in names
                }

        else:
            if depth == 0:
                return {}
            json = {
                name: node.get(depth=depth - 1)
                for name, node in self.children.items()
            }
            self.validate(json)
            return json

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        url = url or []
        if url:
            [
                name,
            ], sub_url = self.extract_child(url)
            return self.children[name].save(data, sub_url)
        else:
            self.validate(data)
            if not self.config.path.exists():
                self.config.path.mkdir()
            for key in data:
                self.children[key].save(data[key])

    def validate(self, data: JSON) -> None:
        for key in data:
            if key not in self.children:
                raise ValueError(
                    f"key={key} not in {list(self.children.keys())} for {self.__class__.__name__}"
                )

    def extract_child(self, url: List[str]) -> Tuple[List[str], List[str]]:
        names, sub_url = url[0].split(","), url[1:]
        names = list(self.children.keys()) if names[0] == "*" else names
        child_class = type(self.children[names[0]])
        for name in names:
            if name not in self.children:
                raise ChildNotFoundError(
                    f"{name} not a children of {self.__class__.__name__}"
                )
            if type(self.children[name]) != child_class:
                raise FilterError("Filter selection has different classes")
        return names, sub_url
