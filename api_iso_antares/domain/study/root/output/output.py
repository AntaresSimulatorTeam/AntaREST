from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            str(i): OutputSimulation(config.next_file(s.get_file()), s)
            for i, s in config.outputs.items()
        }
        FolderNode.__init__(self, children)
