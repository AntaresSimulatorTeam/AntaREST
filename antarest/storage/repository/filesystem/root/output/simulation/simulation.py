from antarest.storage.repository.filesystem.config.model import (
    StudyConfig,
    Simulation,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from antarest.storage.repository.filesystem.root.output.simulation.annualSystemCost import (
    OutputSimulationAnnualSystemCost,
)
from antarest.storage.repository.filesystem.root.output.simulation.checkIntegrity import (
    OutputSimulationCheckIntegrity,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.economy import (
    OutputSimulationMode,
)
from antarest.storage.repository.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from antarest.storage.repository.filesystem.root.output.simulation.simulation_comments import (
    OutputSimulationSimulationComments,
)
from antarest.storage.repository.filesystem.root.output.simulation.simulation_log import (
    OutputSimulationSimulationLog,
)
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)


class OutputSimulation(FolderNode):
    def __init__(self, config: StudyConfig, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                config.next_file("about-the-study")
            ),
            "simulation": OutputSimulationSimulationLog(
                config.next_file("simulation.log")
            ),
            "info": OutputSimulationInfoAntaresOutput(
                config.next_file("info.antares-output")
            ),
        }
        if self.simulation.error:
            children["ts-numbers"] = OutputSimulationTsNumbers(
                config.next_file("ts-numbers")
            )
            children["annualSystemCost"] = OutputSimulationAnnualSystemCost(
                config.next_file("annualSystemCost.txt")
            )
            children["checkIntegrity"] = OutputSimulationCheckIntegrity(
                config.next_file("checkIntegrity.txt")
            )
            children[
                "simulation-comments"
            ] = OutputSimulationSimulationComments(
                config.next_file("simulation-comments.txt")
            )

            if self.simulation.mode == "economy":
                children["economy"] = OutputSimulationMode(
                    config.next_file("economy"), self.simulation
                )

            elif self.simulation.mode == "adequacy":
                children["adequacy"] = OutputSimulationMode(
                    config.next_file("adequacy"), self.simulation
                )

        return children
