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
from typing import List

from typing_extensions import override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.repository import VariantStudyRepository

logger = logging.getLogger(__name__)


class CommandMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(
        self,
        variant_study_repo: VariantStudyRepository,
        command_factory: CommandFactory,
    ):
        self.variant_study_repo = variant_study_repo
        self.command_factory = command_factory
        self.matrix_service = command_factory.command_context.matrix_service
        self.matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> list[MatrixReference]:
        logger.info("Getting all matrices used in variant studies")
        command_blocks: List[CommandBlock] = self.variant_study_repo.get_all_command_blocks()
        matrices_references = []

        def transform_to_command(command_dto: CommandDTO, study_ref: str) -> List[ICommand]:
            try:
                return self.command_factory.to_command(command_dto)
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
                for matrix in command.get_inner_matrices():
                    command_id = str(matrix)
                    mat_reference = MatrixReference(
                        matrix_id=command_id,
                        use_description=f"Used by command {command_id} from variant study {study_id}",
                    )
                    matrices_references.append(mat_reference)

        return matrices_references
