from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcall.mcall import (
    OutputSimulationEconomyMcAll,
)


class OutputSimulationEconomy(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "mc-all": OutputSimulationEconomyMcAll(config.next_file("mc-all"))
        }
        FolderNode.__init__(self, children)
