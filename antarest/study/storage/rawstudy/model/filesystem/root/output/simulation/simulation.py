# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from antarest.output.model.output_type import GEMS_VIEWS_DIR
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.about import OutputSimulationAbout
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.gems_views import GemsViewsFolderNode
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
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLFileNode


class OutputSimulation(FolderNode):
    def __init__(
        self,
        matrix_storage_context: MatrixStorageContext,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        super().__init__(matrix_storage_context, config)
        self.simulation = simulation

    @override
    def build(self) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                self.matrix_storage_context, self.config.next_file("about-the-study")
            ),
            "info": OutputSimulationInfoAntaresOutput(self.config.next_file("info.antares-output")),
        }

        if not self.simulation.error and self.config.path.exists():
            for resource in self.config.path.iterdir():
                if resource.is_file():
                    file_name = resource.name
                    file_extension = resource.suffix
                    if file_extension == ".ini":
                        children[resource.stem] = IniFileNode(self.config.next_file(file_name))
                    elif file_extension in {".yml", ".yaml"}:
                        children[resource.stem] = YAMLFileNode(self.config.next_file(file_name))
                    elif file_extension in {".txt", ".csv", ".log"}:
                        children[resource.stem] = RawFileNode(self.config.next_file(file_name))

            if (self.config.path / "ts-numbers").exists():
                children["ts-numbers"] = OutputSimulationTsNumbers(
                    self.matrix_storage_context, self.config.next_file("ts-numbers")
                )

            if (self.config.path / "ts-generator").exists():
                children["ts-generator"] = OutputSimulationTsGenerator(
                    self.matrix_storage_context, self.config.next_file("ts-generator")
                )

            if (self.config.path / GEMS_VIEWS_DIR).exists():
                children[GEMS_VIEWS_DIR] = GemsViewsFolderNode(
                    self.matrix_storage_context, self.config.next_file(GEMS_VIEWS_DIR)
                )

            for simulation_mode in ["economy", "adequacy"]:
                if (self.config.path / simulation_mode).exists():
                    children[simulation_mode] = OutputSimulationMode(
                        self.matrix_storage_context,
                        self.config.next_file(simulation_mode),
                        self.simulation,
                    )

            if self.simulation.xpansion:
                children["lp"] = Lp(self.matrix_storage_context, self.config.next_file("lp"))
                children["expansion"] = Xpansion(self.matrix_storage_context, self.config.next_file("expansion"))
                if (self.config.path / "sensitivity").exists():
                    children["sensitivity"] = Sensitivity(
                        self.matrix_storage_context, self.config.next_file("sensitivity")
                    )

        return children
