from typing import Optional, List, Union, Dict

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class BucketNode(FolderNode):
    """
    Node to handle structure free, user purpose folder. BucketNode accept any file or sub folder as children.
    """

    def save(
        self,
        data: Union[str, int, bool, float, bytes, JSON],
        url: Optional[List[str]] = None,
    ) -> None:
        assert isinstance(data, Dict)
        for key, value in data.items():
            if isinstance(value, (str, bytes)):
                RawFileNode(self.context, self.config.next_file(key)).save(
                    value
                )
            elif isinstance(value, dict):
                BucketNode(self.context, self.config.next_file(key)).save(
                    value
                )

    def build(self, config: FileStudyTreeConfig) -> TREE:
        if not config.path.exists():
            return dict()

        children: TREE = {}
        for item in sorted(config.path.iterdir()):
            if item.is_file():
                children[item.name] = RawFileNode(
                    self.context, config.next_file(item.name)
                )
            else:
                children[item.name] = BucketNode(
                    self.context, config.next_file(item.name)
                )

        return children

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        return []
