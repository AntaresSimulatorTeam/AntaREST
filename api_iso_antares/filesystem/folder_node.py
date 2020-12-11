from typing import List, Dict, Optional, Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.inode import INode, TREE


class FolderNode(INode[JSON]):
    def __init__(self, config: Config, children: TREE) -> None:
        self.children: TREE = children
        self.config = config

    def get(self, url: Optional[List[str]] = None) -> JSON:
        if url and url != [""]:
            name, sub_url = self.extract_child(url)
            return self.children[name].get(sub_url)
        else:
            json = {name: node.get() for name, node in self.children.items()}
            self.validate(json)
            return json

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        url = url or []
        if url:
            name, sub_url = self.extract_child(url)
            return self.children[name].save(data, sub_url)
        else:
            self.validate(data)
            if not self.config.path.exists():
                self.config.path.mkdir()
            for key in data:
                self.children[key].save(data[key])

    def validate(self, data: JSON) -> None:
        for key in data:
            assert key in self.children

    def extract_child(self, url: List[str]) -> Tuple[str, List[str]]:
        name, sub_url = url[0], url[1:]
        if name not in self.children:
            raise NameError(
                f"{name} not a children of {self.__class__.__name__}"
            )
        return name, sub_url
