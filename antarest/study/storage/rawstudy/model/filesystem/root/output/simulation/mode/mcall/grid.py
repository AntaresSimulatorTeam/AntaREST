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


class OutputSimulationModeMcAllGrid(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "areas": RawFileNode(
                self.context, self.config.next_file("areas.txt")
            ),
            "digest": RawFileNode(
                self.context, self.config.next_file("digest.txt")
            ),
            "links": RawFileNode(
                self.context, self.config.next_file("links.txt")
            ),
            "thermal": RawFileNode(
                self.context, self.config.next_file("thermal.txt")
            ),
        }
        return children
