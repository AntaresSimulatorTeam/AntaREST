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

import typing as t

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Final, override

from antarest.study.business.model.binding_constraint_model import (
    BindingConstraintUpdates,
    update_binding_constraint,
    validate_binding_constraint_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import parse_binding_constraint
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateBindingConstraints(ICommand):
    """
    Command used to update several binding constraints.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINTS
    version: int = 1

    # version 2: type parameters as BindingConstraintUpdates
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    bc_props_by_id: BindingConstraintUpdates

    @model_validator(mode="after")
    def _validate_against_version(self) -> t.Self:
        for parameters in self.bc_props_by_id.values():
            validate_binding_constraint_against_version(self.study_version, parameters)
        return self

    @model_validator(mode="before")
    @classmethod
    def check_version_consistency(cls, values: t.Dict[str, t.Any], info: ValidationInfo) -> t.Dict[str, t.Any]:
        """
        Make sure this object is build with bc props that matches the study version.
        """
        bc_props_by_id = values["bc_props_by_id"]
        study_version = values["study_version"]
        bc_props_by_id_validated = {}
        if info.context and info.context.version < 2:
            for bc_id, bc_props in bc_props_by_id.items():
                bc_props_validated = parse_binding_constraint(study_version, **bc_props)
                bc_props_by_id_validated[bc_id] = bc_props_validated
            values["bc_props_by_id"] = bc_props_by_id_validated
        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        all_constraints = study_data.get_all_constraints()

        new_constraints = []
        for bc_id, props in self.bc_props_by_id.items():
            if bc_id not in all_constraints:
                return command_failed(f"Binding constraint '{bc_id}' does not exist")

            current_constraint = all_constraints[bc_id]
            new_constraint = update_binding_constraint(current_constraint, props)
            new_constraints.append(new_constraint)

        study_data.save_constraints(new_constraints)
        return command_succeeded("All binding constraints updated")

    @override
    def to_dto(self) -> CommandDTO:
        excluded_fields = set(ICommand.model_fields)
        json_command = self.model_dump(mode="json", exclude=excluded_fields, exclude_unset=True)
        return CommandDTO(
            action=self.command_name.value,
            args=json_command,
            version=self._SERIALIZATION_VERSION,
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
