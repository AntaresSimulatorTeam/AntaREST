from AntaREST.storage_api.filesystem.config.model import Config, Simulation
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from AntaREST.storage_api.filesystem.root.output.simulation.annualSystemCost import (
    OutputSimulationAnnualSystemCost,
)
from AntaREST.storage_api.filesystem.root.output.simulation.checkIntegrity import (
    OutputSimulationCheckIntegrity,
)
from AntaREST.storage_api.filesystem.root.output.simulation.mode.economy import (
    OutputSimulationMode,
)
from AntaREST.storage_api.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from AntaREST.storage_api.filesystem.root.output.simulation.simulation_comments import (
    OutputSimulationSimulationComments,
)
from AntaREST.storage_api.filesystem.root.output.simulation.simulation_log import (
    OutputSimulationSimulationLog,
)
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)


class OutputSimulation(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: Config) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                config.next_file("about-the-study")
            ),
            "ts-numbers": OutputSimulationTsNumbers(
                config.next_file("ts-numbers")
            ),
            "annualSystemCost": OutputSimulationAnnualSystemCost(
                config.next_file("annualSystemCost.txt")
            ),
            "checkIntegrity": OutputSimulationCheckIntegrity(
                config.next_file("checkIntegrity.txt")
            ),
            "simulation-comments": OutputSimulationSimulationComments(
                config.next_file("simulation-comments.txt")
            ),
            "simulation": OutputSimulationSimulationLog(
                config.next_file("simulation.log")
            ),
            "info": OutputSimulationInfoAntaresOutput(
                config.next_file("info.antares-output")
            ),
        }
        if self.simulation.mode == "economy":
            children["economy"] = OutputSimulationMode(
                config.next_file("economy"), self.simulation
            )

        elif self.simulation.mode == "adequacy":
            children["adequacy"] = OutputSimulationMode(
                config.next_file("adequacy"), self.simulation
            )

        return children
