from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            str(i): OutputSimulation(config.next_file(s.get_file()), s)
            for i, s in config.outputs.items()
        }
        return children
