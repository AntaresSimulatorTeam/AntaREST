from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.annualSystemCost import (
    OutputSimulationAnnualSystemCost,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.checkIntegrity import (
    OutputSimulationCheckIntegrity,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.economy import (
    OutputSimulationMode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.simulation_comments import (
    OutputSimulationSimulationComments,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.simulation_log import (
    OutputSimulationSimulationLog,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)


class OutputSimulation(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        FolderNode.__init__(self, context, config)
        self.simulation = simulation

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                self.context, config.next_file("about-the-study")
            ),
            "simulation": OutputSimulationSimulationLog(
                self.context, config.next_file("simulation.log")
            ),
            "info": OutputSimulationInfoAntaresOutput(
                self.context, config.next_file("info.antares-output")
            ),
        }
        if not self.simulation.error:
            children["annualSystemCost"] = OutputSimulationAnnualSystemCost(
                self.context, config.next_file("annualSystemCost.txt")
            )
            children["checkIntegrity"] = OutputSimulationCheckIntegrity(
                self.context, config.next_file("checkIntegrity.txt")
            )
            children[
                "simulation-comments"
            ] = OutputSimulationSimulationComments(
                self.context, config.next_file("simulation-comments.txt")
            )

            if config.store_new_set:
                children["ts-numbers"] = OutputSimulationTsNumbers(
                    self.context, config.next_file("ts-numbers")
                )

            if self.simulation.mode == "economy":
                children["economy"] = OutputSimulationMode(
                    self.context, config.next_file("economy"), self.simulation
                )

            elif self.simulation.mode == "adequacy":
                children["adequacy"] = OutputSimulationMode(
                    self.context, config.next_file("adequacy"), self.simulation
                )

        return children
