from typing import Callable, cast
from typing import Any

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode, TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


def traverse_tree(
    url: str,
    node: INode[Any, Any, Any],
    observer: Callable[[str, INode[Any, Any, Any]], None],
) -> None:
    observer(url, node)
    if isinstance(node, FolderNode):
        for key, child in node.build().items():
            traverse_tree(url + "/" + key, child, observer)
