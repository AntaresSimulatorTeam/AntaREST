from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from api_iso_antares.filesystem.root.output.simulation.economy.economy import (
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

        elif (
            simulation.mode == "adequacy"
        ):  # TODO don't reuse OutputSimulationEconomy
            children["adequacy"] = OutputSimulationEconomy(
                config.next_file("adequacy"), simulation
            )

        FolderNode.__init__(self, config, children)
