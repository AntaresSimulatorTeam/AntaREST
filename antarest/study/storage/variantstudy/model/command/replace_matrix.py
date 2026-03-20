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
from pathlib import Path
from typing import List

from pydantic import Field, ValidationInfo, field_validator
from typing_extensions import override

from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.raw_path_to_matrix_mapper import RawPathToMatrixMapper
from antarest.study.storage.variantstudy.business.utils import AliasDecoder, strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    InnerMatrices,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceMatrix(ICommand):
    """
    Command used to replace a matrice in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_MATRIX

    # Command parameters
    # ==================

    target: str
    matrix: List[List[MatrixData]] | str = Field(validate_default=True)

    @field_validator("matrix", mode="before")
    def matrix_validator(cls, matrix: List[List[MatrixData]] | str, values: ValidationInfo) -> str:
        return validate_matrix(matrix, values.data)

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        if self.target[0] == "@":
            self.target = AliasDecoder.decode(self.target, self.study_version)

        mapper = RawPathToMatrixMapper(study_data)
        assert isinstance(self.matrix, str)
        mapper.save_matrix_from_path(Path(self.target), self.matrix)
        return command_succeeded(message=f"Matrix '{self.target}' has been successfully replaced.", result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={"target": self.target, "matrix": strip_matrix_protocol(self.matrix)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> InnerMatrices:
        assert_this(isinstance(self.matrix, str))
        return InnerMatrices(matrices=[strip_matrix_protocol(self.matrix)])
