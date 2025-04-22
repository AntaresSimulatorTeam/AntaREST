# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
from typing_extensions import override

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.about import OutputSimulationAbout
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.economy import OutputSimulationMode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_generator.ts_generator import (
    OutputSimulationTsGenerator,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.lp import Lp
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.sensitivity import Sensitivity
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.xpansion.xpansion import Xpansion


class OutputSimulation(FolderNode):
    def __init__(
        self,
        context: MatrixUriMapper,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        super().__init__(context, config)
        self.simulation = simulation

    @override
    def build(self) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(self.context, self.config.next_file("about-the-study")),
            "simulation": RawFileNode(self.context, self.config.next_file("simulation.log")),
            "info": OutputSimulationInfoAntaresOutput(self.config.next_file("info.antares-output")),
            "antares-out": RawFileNode(self.context, self.config.next_file("antares-out.log")),
            "antares-err": RawFileNode(self.context, self.config.next_file("antares-err.log")),
        }

        if not self.simulation.error:
            for file in ["annualSystemCost", "checkIntegrity", "simulation-comments"]:
                file_name = f"{file}.txt"
                if (self.config.path / file_name).exists():
                    children[file] = RawFileNode(self.context, self.config.next_file(file_name))

            file_name = "execution_info"
            if (self.config.path / f"{file_name}.ini").exists():
                children[file_name] = IniFileNode(self.config.next_file(f"{file_name}.ini"))

            if (self.config.path / "ts-numbers").exists():
                children["ts-numbers"] = OutputSimulationTsNumbers(self.context, self.config.next_file("ts-numbers"))

            if (self.config.path / "ts-generator").exists():
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
                children["expansion"] = Xpansion(self.context, self.config.next_file("expansion"))
                children["sensitivity"] = Sensitivity(self.context, self.config.next_file("sensitivity"))

        return children
