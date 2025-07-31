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

from pydantic import TypeAdapter, model_validator
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

_CONSTRAINTS_TYPE_ADAPTER = TypeAdapter(type=STStorageAdditionalConstraintUpdates)


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
            for storage_id, values in value.items():
                new_constraints = []
                all_constraints_per_storage = study_data.get_st_storage_additional_constraints(area_id, storage_id)
                existing_ids = {c.id: index for index, c in enumerate(all_constraints_per_storage)}

                for constraint_id, updated_constraint in values.items():
                    if constraint_id not in existing_ids:
                        return command_failed(
                            f"Constraint {constraint_id} not found for short-term storage {storage_id} in area '{area_id}'."
                        )

                    current_constraint = all_constraints_per_storage[existing_ids[constraint_id]]
                    new_constraint = update_st_storage_constraint(current_constraint, updated_constraint)
                    new_constraints.append(new_constraint)

                study_data.save_st_storage_additional_constraints(area_id, storage_id, new_constraints)

        return command_succeeded("The short-term storage additional constraints were successfully updated.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "additional_constraint_properties": _CONSTRAINTS_TYPE_ADAPTER.dump_python(
                    self.additional_constraint_properties, exclude_defaults=True
                )
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
