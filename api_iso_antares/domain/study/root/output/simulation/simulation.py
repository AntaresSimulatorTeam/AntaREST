from api_iso_antares.domain.study.config import Config, Simulation
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from api_iso_antares.domain.study.root.output.simulation.economy.economy import (
    OutputSimulationEconomy,
)


class OutputSimulation(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                config.next_file("about-the-study")
            ),
        }
        if simulation.mode == "economy":
            children["economy"] = OutputSimulationEconomy(
                config.next_file("economy"), simulation
            )

        FolderNode.__init__(self, children)
