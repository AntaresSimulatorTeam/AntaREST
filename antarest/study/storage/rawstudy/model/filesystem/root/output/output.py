from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            str(s.get_file()): OutputSimulation(
                self.context, config.next_file(s.get_file()), s
            )
            for i, s in config.outputs.items()
        }
        return children
