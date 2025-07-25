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

from typing import List, Optional

from pydantic import Field, ValidationInfo, field_validator
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
from antarest.study.storage.variantstudy.business.utils import AliasDecoder, strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
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
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if self.target[0] == "@":
            self.target = AliasDecoder.decode(self.target, study_data)

        replace_matrix_data: JSON = {}
        target_matrix = replace_matrix_data
        url = self.target.split("/")
        for element in url[:-1]:
            target_matrix[element] = {}
            target_matrix = target_matrix[element]

        target_matrix[url[-1]] = self.matrix

        try:
            last_node = study_data.tree.get_node(url)
            assert_this(isinstance(last_node, MatrixNode))
        except (KeyError, ChildNotFoundError):
            return command_failed(message=f"Path '{self.target}' does not exist.")
        except AssertionError:
            return command_failed(message=f"Path '{self.target}' does not target a matrix.")

        study_data.tree.save(replace_matrix_data)
        return command_succeeded(message=f"Matrix '{self.target}' has been successfully replaced.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={
                "target": self.target,
                "matrix": strip_matrix_protocol(self.matrix),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        assert_this(isinstance(self.matrix, str))
        return [strip_matrix_protocol(self.matrix)]
