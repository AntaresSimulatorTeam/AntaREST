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

import logging
from typing import List, Tuple

from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class VariantCommandsExtractor:
    def __init__(self, matrix_service: ISimpleMatrixService, patch_service: PatchService):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(self.matrix_service)
        self.generator_matrix_constants.init_constant_matrices()
        self.command_extractor = CommandExtractor(self.matrix_service, patch_service=patch_service)

    def extract(self, study: FileStudy) -> List[CommandDTO]:
        stopwatch = StopWatch()
        study_tree = study.tree
        study_config = study.config
        # noinspection SpellCheckingInspection
        study_commands: List[ICommand] = [
            self.command_extractor.generate_update_config(study_tree, ["settings", "generaldata"]),
            self.command_extractor.generate_update_config(
                study_tree,
                ["settings", "scenariobuilder"],
            ),
            self.command_extractor.generate_update_config(study_tree, ["layers", "layers"]),
        ]

        stopwatch.log_elapsed(lambda x: logger.info(f"General command extraction done in {x}s"))

        all_links_commands: List[ICommand] = []
        for area_id in study_config.areas:
            (
                area_commands,
                links_commands,
            ) = self.command_extractor.extract_area(study, area_id)
            study_commands += area_commands
            all_links_commands += links_commands
        study_commands += all_links_commands

        # correlations
        for cat in ["load", "wind", "solar", "hydro"]:
            study_commands.append(
                self.command_extractor.generate_update_config(
                    study_tree,
                    ["input", cat, "prepro", "correlation"],
                )
            )

        # sets and all area config (weird it is found in thermal..)
        study_commands.append(
            self.command_extractor.generate_update_config(
                study_tree,
                ["input", "thermal", "areas"],
            )
        )
        for set_id in study_config.sets:
            study_commands += self.command_extractor.extract_district(study, set_id)

        # binding constraints
        # noinspection SpellCheckingInspection
        binding_config = study_tree.get(["input", "bindingconstraints", "bindingconstraints"])
        for binding_id, binding_data in binding_config.items():
            study_commands += self.command_extractor.extract_binding_constraint(study, binding_id, binding_data)

        stopwatch.log_elapsed(lambda x: logger.info(f"Binding command extraction done in {x}s"))

        stopwatch.log_elapsed(lambda x: logger.info(f"Command extraction done in {x}s"), True)

        study_commands += self.command_extractor.extract_comments(study=study)
        return [command.to_dto() for command in study_commands]
