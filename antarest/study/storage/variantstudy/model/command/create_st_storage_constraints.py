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


from typing import List, Optional, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.model import LowerCaseId
from antarest.study.business.model.sts_model import STStorageAdditionalConstraintCreation, create_st_storage_constraint
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


# noinspection SpellCheckingInspection
class CreateSTStorageAdditionalConstraints(ICommand):
    """
    Command used to create several short-term storage constraints in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS

    # Command parameters
    # ==================

    area_id: AreaId
    storage_id: LowerCaseId
    constraints: list[STStorageAdditionalConstraintCreation]

    @model_validator(mode="after")
    def _validate_against_version(self) -> Self:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(
                f"Command '{self.command_name.value}' is only available since v9.2 and you're in {self.study_version}"
            )
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.st_storage_exists(self.area_id, self.storage_id):
            return command_failed(
                f"Short-term storage '{self.storage_id}' inside area '{self.area_id}' does not exist."
            )

        constraints = [create_st_storage_constraint(constraint) for constraint in self.constraints]

        # Checks if the constraint already exists in the study
        existing_constraints = study_data.get_st_storage_additional_constraints(self.area_id, self.storage_id)
        existing_ids = {c.id for c in existing_constraints}
        for constraint in constraints:
            if constraint.id in existing_ids:
                return command_failed(f"Short-term storage constraint '{constraint.id}' already exists.")

        # Save the new constraints
        study_data.save_st_storage_additional_constraints(self.area_id, {self.storage_id: constraints})
        # Save the default matrices
        null_matrix = self.command_context.generator_matrix_constants.get_null_matrix()
        for constraint in constraints:
            study_data.save_st_storage_constraint_matrix(self.area_id, constraint.id, null_matrix)

        return command_succeeded(
            f"Short-term storage additional constraints successfully added to area '{self.area_id}'."
        )

    @override
    def to_dto(self) -> CommandDTO:
        constraints = [c.model_dump(mode="json", by_alias=True, exclude_none=True) for c in self.constraints]
        args = {"area_id": self.area_id, "storage_id": self.storage_id, "constraints": constraints}
        return CommandDTO(action=self.command_name.value, args=args, study_version=self.study_version)

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
