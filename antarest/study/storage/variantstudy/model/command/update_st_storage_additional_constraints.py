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
from typing import Any, List, Optional, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.sts_model import (
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintUpdates,
    update_st_storage_constraint,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateSTStorageAdditionalConstraints(ICommand):
    """
    Command used to update several short-term storage additional constraints
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS

    # Command parameters
    # ==================

    additional_constraint_properties: STStorageAdditionalConstraintUpdates

    @model_validator(mode="after")
    def validate_against_version(self) -> Self:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(
                f"Command '{self.command_name.value}' is only available since v9.2 and you're in {self.study_version}"
            )
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, value in self.additional_constraint_properties.items():
            all_constraints_per_area = study_data.get_st_storage_additional_constraints_for_area(area_id)

            new_constraints: dict[str, list[STStorageAdditionalConstraint]] = {}
            if not all_constraints_per_area:
                return command_failed(f"The area '{area_id}' is not found.")

            for storage_id, updated_constraints in value.items():
                if storage_id not in all_constraints_per_area:
                    return command_failed(f"Short-term storage {storage_id} not found in area '{area_id}'.")
                existing_ids = {c.id: index for index, c in enumerate(all_constraints_per_area[storage_id])}
                for upd_constraint in updated_constraints:
                    if upd_constraint.id not in existing_ids:
                        return command_failed(
                            f"Constraint {upd_constraint.id} not found for short-term storage {storage_id} in area '{area_id}'."
                        )

                    current_constraint = all_constraints_per_area[storage_id][existing_ids[upd_constraint.id]]
                    new_constraint = update_st_storage_constraint(current_constraint, upd_constraint)
                    new_constraints.setdefault(storage_id, []).append(new_constraint)

            study_data.save_st_storage_additional_constraints(area_id, new_constraints)

        return command_succeeded("The short-term storage additional constraints were successfully updated.")

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, list[dict[str, Any]]]] = {}

        for area_id, value in self.additional_constraint_properties.items():
            for storage_id, updated_constraints in value.items():
                for constraint in updated_constraints:
                    body = constraint.model_dump(mode="json", exclude_unset=True)
                    args.setdefault(area_id, {}).setdefault(storage_id, []).append(body)

        return CommandDTO(
            action=self.command_name.value,
            args={"additional_constraint_properties": args},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
