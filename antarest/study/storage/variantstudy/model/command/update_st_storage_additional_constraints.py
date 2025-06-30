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
        all_constraints = study_data.get_all_st_storage_additional_constraints()

        for area_id, value in self.additional_constraint_properties.items():
            if area_id not in all_constraints:
                return command_failed(f"The area '{area_id}' is not found.")

            existing_constraints_ids = {c.id: index for index, c in enumerate(all_constraints[area_id])}
            new_constraints = []
            for constraint_id, new_properties in value.items():
                if constraint_id not in existing_constraints_ids:
                    return command_failed(
                        f"The short-term storage additional constraint'{constraint_id}' in the area '{area_id}' is not found."
                    )

                current_constraint = all_constraints[area_id][existing_constraints_ids[constraint_id]]
                new_constraint = update_st_storage_constraint(current_constraint, new_properties)
                new_constraints.append(new_constraint)

            study_data.save_st_storage_additional_constraints(area_id, new_constraints)

        return command_succeeded("The short-term storage additional constraints were successfully updated.")

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}

        for area_id, value in self.additional_constraint_properties.items():
            for constraint_id, properties in value.items():
                args.setdefault(area_id, {})[constraint_id] = properties.model_dump(mode="json", exclude_unset=True)

        return CommandDTO(
            action=self.command_name.value,
            args={"additional_constraint_properties": args},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
