import logging
from typing import List, Tuple

from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils_extractor import (
    CommandExtraction,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class VariantCommandsExtractor:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(
            self.matrix_service
        )
        self.command_extractor = CommandExtraction(self.matrix_service)

    def extract(self, study: FileStudy) -> List[CommandDTO]:
        stopwatch = StopWatch()
        study_tree = study.tree
        study_config = study.config
        study_commands: List[ICommand] = []

        study_commands.append(
            self.command_extractor.generate_update_config(
                study_tree, ["settings", "generaldata"]
            )
        )
        study_commands.append(
            self.command_extractor.generate_update_config(
                study_tree,
                ["settings", "scenariobuilder"],
            )
        )
        study_commands.append(
            self.command_extractor.generate_update_config(
                study_tree, ["layers", "layers"]
            )
        )
        # todo create something out of variant manager commands to replace single rawnode files ?
        # study_commands.append(
        #     self._generate_update_config(
        #         study_tree, ["settings", "comments"]
        #     )
        # )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"General command extraction done in {x}s")
        )

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
        for type in ["load", "wind", "solar", "hydro"]:
            study_commands.append(
                self.command_extractor.generate_update_config(
                    study_tree,
                    ["input", type, "prepro", "correlation"],
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
            study_commands += self.command_extractor.extract_district(
                study, set_id
            )

        # binding constraints
        binding_config = study_tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        for binding_id, binding_data in binding_config.items():
            study_commands += (
                self.command_extractor.extract_binding_constraint(
                    study, binding_id, binding_data
                )
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Binding command extraction done in {x}s")
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command extraction done in {x}s"), True
        )

        study_commands += self.command_extractor.extract_comments(study=study)
        return [command.to_dto() for command in study_commands]

    def diff(
        self, base: List[CommandDTO], variant: List[CommandDTO]
    ) -> List[ICommand]:
        stopwatch = StopWatch()
        command_factory = CommandFactory(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
        )
        logger.info("Parsing commands")
        base_commands: List[ICommand] = []
        for command in base:
            base_commands += command_factory.to_icommand(command)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Base commands parsed in {x}s")
        )
        variant_commands: List[ICommand] = []
        for command in variant:
            variant_commands += command_factory.to_icommand(command)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Variant commands parsed in {x}s")
        )

        logger.info("Computing commands diff")
        added_commands: List[Tuple[int, ICommand]] = []
        missing_commands: List[Tuple[ICommand, int]] = []
        modified_commands: List[Tuple[int, ICommand, ICommand]] = []
        order = 10
        for variant_command in variant_commands:
            order += 1
            found = False
            for base_command in base_commands:
                if variant_command.match(base_command):
                    if not variant_command.match(base_command, True):
                        modified_commands.append(
                            (order, variant_command, base_command)
                        )
                    found = True
                    break
            if not found:
                added_commands.append((order, variant_command))
        stopwatch.log_elapsed(
            lambda x: logger.info(f"First diff pass done in {x}s")
        )
        logger.info(f"Found {len(added_commands)} added commands")
        logger.info(f"Found {len(modified_commands)} modified commands")
        index = 0
        for base_command in base_commands:
            found = False
            for variant_command in variant_commands:
                if base_command.match(variant_command):
                    found = True
                    break
            if not found:
                missing_commands.append((base_command, index))
            index += 1
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Second diff pass done in {x}s")
        )
        logger.info(f"Found {len(missing_commands)} missing commands")

        first_commands: List[Tuple[int, ICommand]] = []
        last_commands: List[Tuple[int, ICommand]] = []
        logger.info(f"Computing new diff commands")
        for command_obj, index in missing_commands:
            logger.info(f"Reverting {command_obj.match_signature()}")
            if command_obj.command_name == CommandName.REMOVE_AREA:
                command_list = first_commands
                priority = 0
            elif (
                command_obj.command_name == CommandName.REMOVE_LINK
                or command_obj.command_name == CommandName.REMOVE_CLUSTER
            ):
                command_list = first_commands
                priority = 1
            elif (
                command_obj.command_name == CommandName.UPDATE_CONFIG
                or command_obj.command_name == CommandName.REPLACE_MATRIX
                or command_obj.command_name == CommandName.UPDATE_COMMENTS
            ):
                command_list = first_commands
                priority = 2
            elif command_obj.command_name == CommandName.CREATE_AREA:
                command_list = last_commands
                priority = 3
            elif (
                command_obj.command_name == CommandName.CREATE_CLUSTER
                or command_obj.command_name == CommandName.CREATE_LINK
            ):
                command_list = last_commands
                priority = 2
            elif (
                command_obj.command_name == CommandName.CREATE_LINK
                or command_obj.command_name
                == CommandName.CREATE_BINDING_CONSTRAINT
                or command_obj.command_name == CommandName.CREATE_DISTRICT
            ):
                command_list = last_commands
                priority = 1
            else:
                command_list = first_commands
                priority = 3

            command_list.extend(
                [
                    (priority, command)
                    for command in command_obj.revert(base_commands[:index])
                ]
            )
        for order, variant_command, base_command in modified_commands:
            logger.info(
                f"Generating diff command for {variant_command.match_signature()}"
            )
            first_commands += [
                (order, command)
                for command in base_command.create_diff(variant_command)
            ]
        for ordered_command in added_commands:
            first_commands.append(ordered_command)

        first_commands.sort(key=lambda x: x[0])
        last_commands.sort(key=lambda x: x[0])

        diff_commands = [
            ordered_command[1] for ordered_command in first_commands
        ] + [ordered_command[1] for ordered_command in last_commands]
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Diff commands generation done in {x}s"),
            since_start=True,
        )
        logger.info(f"Diff commands total : {len(diff_commands)}")
        return diff_commands
