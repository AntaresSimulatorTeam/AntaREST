from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


class BucketNode(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        if not config.path.exists():
            return dict()

        children: TREE = {}
        for item in config.path.iterdir():
            if item.is_file():
                children[item.name] = RawFileNode(config.next_file(item.name))
            else:
                children[item.name] = BucketNode(config.next_file(item.name))

        return children

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        return []
