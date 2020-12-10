from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from api_iso_antares.filesystem.root.output.simulation.annualSystemCost import (
    OutputSimulationAnnualSystemCost,
)
from api_iso_antares.filesystem.root.output.simulation.checkIntegrity import (
    OutputSimulationCheckIntegrity,
)
from api_iso_antares.filesystem.root.output.simulation.economy.economy import (
    OutputSimulationEconomy,
)
from api_iso_antares.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from api_iso_antares.filesystem.root.output.simulation.simulation_comments import (
    OutputSimulationSimulationComments,
)
from api_iso_antares.filesystem.root.output.simulation.simulation_log import (
    OutputSimulationSimulationLog,
)
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)


class OutputSimulation(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
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
