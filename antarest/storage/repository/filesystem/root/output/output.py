from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            str(i): OutputSimulation(config.next_file(s.get_file()), s)
            for i, s in config.outputs.items()
        }
        return children
