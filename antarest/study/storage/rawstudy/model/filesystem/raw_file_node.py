from typing import List, Optional

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import (
    LazyNode,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)


class RawFileNode(LazyNode[bytes, bytes, str]):
    """
    Basic left which handle text file as like with any parsing / serialization
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        LazyNode.__init__(self, config=config, context=context)

    def build(self, config: FileStudyTreeConfig) -> TREE:
        pass  # end node has nothing to build

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"file://{self.config.path.name}"

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> bytes:
        return self.config.path.read_bytes()

    def dump(self, data: bytes, url: Optional[List[str]] = None) -> None:
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        self.config.path.write_bytes(data)

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        if not self.config.path.exists():
            msg = f"{self.config.path} not exist"
            if raising:
                raise ValueError(msg)
            return [msg]
        return []

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node
