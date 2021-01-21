from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            str(i): OutputSimulation(config.next_file(s.get_file()), s)
            for i, s in config.outputs.items()
        }
        return children
