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
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union, cast

from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.utils import update_antares_info
from antarest.study.storage.variantstudy.model.command.common import CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO, NewDetailsDTO

logger = logging.getLogger(__name__)

APPLY_CALLBACK = Callable[[ICommand, Union[FileStudyTreeConfig, FileStudy], Optional[ICommandListener]], CommandOutput]


class CmdNotifier:
    def __init__(self, study_id: str, total_count: int) -> None:
        self.index = 0
        self.study_id = study_id
        self.total_count = total_count

    def __call__(self, x: float) -> None:
        logger.info(f"Command {self.index}/{self.total_count} [{self.study_id}] applied in {x}s")


class VariantCommandGenerator:
    def __init__(self, study_factory: StudyFactory) -> None:
        self.study_factory = study_factory

    @staticmethod
    def _generate(
        commands: List[List[ICommand]],
        data: Union[FileStudy, FileStudyTreeConfig],
        applier: APPLY_CALLBACK,
        metadata: Optional[VariantStudy] = None,
        notifier: Optional[Callable[[int, bool, str], None]] = None,
        listener: Optional[ICommandListener] = None,
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()
        # Apply commands
        results: GenerationResultInfoDTO = GenerationResultInfoDTO(success=True, details=[])

        logger.info("Applying commands")
        study_id = "-" if metadata is None else metadata.id

        # flatten the list of commands
        all_commands = [command for command_batch in commands for command in command_batch]

        # Prepare the stopwatch
        cmd_notifier = CmdNotifier(study_id, len(all_commands))
        stopwatch.reset_current()

        # Store all the outputs
        for index, cmd in enumerate(all_commands, 1):
            try:
                output = applier(cmd, data, listener)
            except Exception as e:
                # Unhandled exception
                output = CommandOutput(
                    status=False,
                    message=f"Error while applying command {cmd.command_name}",
                )
                logger.error(output.message, exc_info=e)

            # noinspection PyTypeChecker
            detail: NewDetailsDTO = {
                "id": uuid.UUID(int=0) if cmd.command_id is None else cmd.command_id,
                "name": cmd.command_name.value,
                "status": output.status,
                "msg": output.message,
            }
            results.details.append(detail)

            if notifier:
                notifier(index - 1, output.status, output.message)

            cmd_notifier.index = index
            stopwatch.log_elapsed(cmd_notifier)

            # stop variant generation as soon as a command fails
            if not output.status:
                logger.error(f"Command {cmd.command_name} failed: {output.message}")
                break

        results.success = all(detail["status"] for detail in results.details)  # type: ignore

        data_type = isinstance(data, FileStudy)
        stopwatch.log_elapsed(
            lambda x: logger.info(
                f"Variant generation done in {x}s" if data_type else f"Variant light generation done in {x}s"
            ),
            since_start=True,
        )
        return results

    def generate(
        self,
        commands: List[List[ICommand]],
        dest_path: Path,
        metadata: Optional[VariantStudy] = None,
        delete_on_failure: bool = True,
        notifier: Optional[Callable[[int, bool, str], None]] = None,
        listener: Optional[ICommandListener] = None,
    ) -> GenerationResultInfoDTO:
        # Build file study
        logger.info("Building study tree")
        study = self.study_factory.create_from_fs(dest_path, "", use_cache=False)
        if metadata:
            update_antares_info(metadata, study.tree, update_author=True)

        results = VariantCommandGenerator._generate(
            commands,
            study,
            lambda command, data, listener: command.apply(cast(FileStudy, data), listener),
            metadata,
            notifier,
        )

        if not results.success and delete_on_failure:
            shutil.rmtree(dest_path)
        return results

    def generate_config(
        self,
        commands: List[List[ICommand]],
        config: FileStudyTreeConfig,
        metadata: Optional[VariantStudy] = None,
        notifier: Optional[Callable[[int, bool, str], None]] = None,
    ) -> Tuple[GenerationResultInfoDTO, FileStudyTreeConfig]:
        logger.info("Building config (light generation)")
        results = VariantCommandGenerator._generate(
            commands,
            config,
            lambda command, data, listener: command.apply_config(cast(FileStudyTreeConfig, data)),
            metadata,
            notifier,
        )
        # because the config has the parent id there
        if metadata:
            config.study_id = metadata.id
        return results, config
