from functools import reduce

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
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.economy import (
    OutputSimulationMode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_generator.ts_generator import (
    OutputSimulationTsGenerator,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.lp import (
    Lp,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.sensitivity import (
    Sensitivity,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.xpansion import (
    Xpansion,
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

    def build(self) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                self.context, self.config.next_file("about-the-study")
            ),
            "simulation": RawFileNode(
                self.context, self.config.next_file("simulation.log")
            ),
            "info": OutputSimulationInfoAntaresOutput(
                self.context, self.config.next_file("info.antares-output")
            ),
            "antares-out": RawFileNode(
                self.context, self.config.next_file("antares-out.log")
            ),
            "antares-err": RawFileNode(
                self.context, self.config.next_file("antares-err.log")
            ),
        }

        if not self.simulation.error:

            children["annualSystemCost"] = RawFileNode(
                self.context, self.config.next_file("annualSystemCost.txt")
            )
            children["checkIntegrity"] = RawFileNode(
                self.context, self.config.next_file("checkIntegrity.txt")
            )
            children["simulation-comments"] = RawFileNode(
                self.context, self.config.next_file("simulation-comments.txt")
            )

            if self.config.store_new_set:
                children["ts-numbers"] = OutputSimulationTsNumbers(
                    self.context, self.config.next_file("ts-numbers")
                )

            if self.config.archive_input_series:
                children["ts-generator"] = OutputSimulationTsGenerator(
                    self.context, self.config.next_file("ts-generator")
                )

            if self.simulation.mode == "economy":
                children["economy"] = OutputSimulationMode(
                    self.context,
                    self.config.next_file("economy"),
                    self.simulation,
                )

            elif self.simulation.mode == "adequacy":
                children["adequacy"] = OutputSimulationMode(
                    self.context,
                    self.config.next_file("adequacy"),
                    self.simulation,
                )

            if self.simulation.xpansion:
                children["lp"] = Lp(self.context, self.config.next_file("lp"))
                children["expansion"] = Xpansion(
                    self.context, self.config.next_file("expansion")
                )
                children["sensitivity"] = Sensitivity(
                    self.context, self.config.next_file("sensitivity")
                )

        return children
