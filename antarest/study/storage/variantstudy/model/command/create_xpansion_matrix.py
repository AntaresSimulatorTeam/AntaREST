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

from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, ValidationInfo, field_validator
from typing_extensions import override

from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.xpansion_common import (
    apply_config_create_resource_commands,
    apply_create_resource_commands,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class AbstractCreateXpansionMatrix(ICommand):
    # Command parameters
    # ==================

    filename: str
    matrix: List[List[MatrixData]] | str = Field(validate_default=True)

    @field_validator("matrix", mode="before")
    def matrix_validator(cls, matrix: List[List[MatrixData]] | str, values: ValidationInfo) -> str:
        return validate_matrix(matrix, values.data)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "filename": self.filename,
                "matrix": strip_matrix_protocol(self.matrix),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        assert_this(isinstance(self.matrix, str))
        return [strip_matrix_protocol(self.matrix)]


class CreateXpansionWeight(AbstractCreateXpansionMatrix):
    """
    Command used to create a xpansion weight matrix.
    """

    command_name: CommandName = CommandName.CREATE_XPANSION_WEIGHT

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return apply_config_create_resource_commands(self.filename, XpansionResourceFileType.WEIGHTS)

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        return apply_create_resource_commands(self.filename, self.matrix, study_data, XpansionResourceFileType.WEIGHTS)


class CreateXpansionCapacity(AbstractCreateXpansionMatrix):
    """
    Command used to create a xpansion capacity matrix.
    """

    command_name: CommandName = CommandName.CREATE_XPANSION_CAPACITY

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return apply_config_create_resource_commands(self.filename, XpansionResourceFileType.CAPACITIES)

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        return apply_create_resource_commands(
            self.filename, self.matrix, study_data, XpansionResourceFileType.CAPACITIES
        )
