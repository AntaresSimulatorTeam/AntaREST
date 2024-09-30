# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

    def diff(
        self,
        base: List[CommandDTO],
        variant: List[CommandDTO],
        empty_study: FileStudy,
    ) -> List[ICommand]:
        stopwatch = StopWatch()
        command_factory = CommandFactory(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
            patch_service=self.command_extractor.patch_service,
        )

        logger.info("Parsing commands")
        base_commands = command_factory.to_commands(base)
        stopwatch.log_elapsed(lambda x: logger.info(f"Base commands parsed in {x}s"))
        variant_commands = command_factory.to_commands(variant)
        stopwatch.log_elapsed(lambda x: logger.info(f"Variant commands parsed in {x}s"))

        logger.info("Computing commands diff")
        added_commands: List[Tuple[int, ICommand]] = []
        missing_commands: List[Tuple[ICommand, int]] = []
        modified_commands: List[Tuple[int, ICommand, ICommand]] = []
        for order, variant_command in enumerate(variant_commands, start=11):
            for base_command in base_commands:
                if variant_command.match(base_command):
                    if not variant_command.match(base_command, True):
                        modified_commands.append((order, variant_command, base_command))
                    break
            else:
                # not found
                added_commands.append((order, variant_command))
        stopwatch.log_elapsed(lambda x: logger.info(f"First diff pass done in {x}s"))
        logger.info(f"Found {len(added_commands)} added commands")
        logger.info(f"Found {len(modified_commands)} modified commands")
        for index, base_command in enumerate(base_commands):
            found = any(base_command.match(variant_command) for variant_command in variant_commands)
            if not found:
                missing_commands.append((base_command, index))
        stopwatch.log_elapsed(lambda x: logger.info(f"Second diff pass done in {x}s"))
        logger.info(f"Found {len(missing_commands)} missing commands")

        first_commands: List[Tuple[int, ICommand]] = []
        last_commands: List[Tuple[int, ICommand]] = []
        logger.info("Computing new diff commands")
        for command_obj, index in missing_commands:
            logger.info(f"Reverting {command_obj.match_signature()}")
            if command_obj.command_name == CommandName.REMOVE_AREA:
                command_list = first_commands
                priority = 0
            elif command_obj.command_name in [
                CommandName.REMOVE_LINK,
                CommandName.REMOVE_THERMAL_CLUSTER,
                CommandName.REMOVE_RENEWABLES_CLUSTER,
                CommandName.REMOVE_ST_STORAGE,
            ]:
                command_list = first_commands
                priority = 1
            elif command_obj.command_name in [
                CommandName.UPDATE_CONFIG,
                CommandName.REPLACE_MATRIX,
                CommandName.UPDATE_COMMENTS,
            ]:
                command_list = first_commands
                priority = 2
            elif command_obj.command_name == CommandName.CREATE_AREA:
                command_list = last_commands
                priority = 3
            elif command_obj.command_name in [
                CommandName.CREATE_ST_STORAGE,
                CommandName.CREATE_RENEWABLES_CLUSTER,
                CommandName.CREATE_THERMAL_CLUSTER,
                CommandName.CREATE_LINK,
            ]:
                command_list = last_commands
                priority = 2
            elif command_obj.command_name in [
                CommandName.CREATE_BINDING_CONSTRAINT,
                CommandName.CREATE_DISTRICT,
            ]:
                command_list = last_commands
                priority = 1
            else:
                command_list = first_commands
                priority = 3

            # noinspection SpellCheckingInspection
            command_reverter = CommandReverter()
            command_list.extend(
                [
                    (priority, command)
                    for command in command_reverter.revert(
                        command_obj,
                        history=base_commands[:index],
                        base=empty_study,
                    )
                ]
            )
        for order, variant_command, base_command in modified_commands:
            logger.info(f"Generating diff command for {variant_command.match_signature()}")
            first_commands += [(order, command) for command in base_command.create_diff(variant_command)]
        for ordered_command in added_commands:
            first_commands.append(ordered_command)

        first_commands.sort(key=lambda x: x[0])
        last_commands.sort(key=lambda x: x[0])

        diff_commands = [ordered_command[1] for ordered_command in first_commands] + [
            ordered_command[1] for ordered_command in last_commands
        ]
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Diff commands generation done in {x}s"),
            since_start=True,
        )
        logger.info(f"Diff commands total : {len(diff_commands)}")
        return diff_commands
