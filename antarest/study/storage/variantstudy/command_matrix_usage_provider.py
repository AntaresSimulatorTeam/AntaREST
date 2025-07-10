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
from typing import List

from typing_extensions import override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import MatrixService
from antarest.study.service import StudyService, logger
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CommandMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, study_service: StudyService, matrix_service: MatrixService):
        self.study_service = study_service
        self.variant_study_service = self.study_service.storage_service.variant_study_service
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> list[MatrixReference]:
        logger.info("Getting all matrices used in variant studies")
        command_blocks: List[CommandBlock] = self.variant_study_service.repository.get_all_command_blocks()
        matrices_references = []

        def transform_to_command(command_dto: CommandDTO, study_ref: str) -> List[ICommand]:
            try:
                return self.variant_study_service.command_factory.to_command(command_dto)
            except Exception as e:
                logger.warning(
                    f"Failed to parse command {command_dto} (from study {study_ref}) !",
                    exc_info=e,
                )
            return []

        variant_study_commands = [cmd for c in command_blocks for cmd in transform_to_command(c.to_dto(), c.study_id)]
        for block in command_blocks:
            study_id = block.study_id
            for command in variant_study_commands:
                for matrix in command:
                    mat_reference = MatrixReference(
                        matrix_id=matrix, use_description=f"Used by {command.command_id} from study {study_id}"
                    )
                    matrices_references.append(mat_reference)

        return matrices_references
