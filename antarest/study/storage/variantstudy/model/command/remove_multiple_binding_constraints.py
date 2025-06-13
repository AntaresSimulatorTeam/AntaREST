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

from typing import Any, List, Optional

from pydantic import model_validator
from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveMultipleBindingConstraints(ICommand):
    """
    Command used to remove multiple binding constraints at once.
    """

    command_name: CommandName = CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS

    # Properties of the `REMOVE_MULTIPLE_BINDING_CONSTRAINTS` command:
    ids: List[str]

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Handle the legacy command `RemoveBindingConstraint`
        if "id" in values:
            values["ids"] = [values.pop("id")]
        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        all_bcs = study_data.get_all_constraints()
        constraints = []
        for bc_id in self.ids:
            if bc_id not in all_bcs:
                return command_failed(f"Binding constraint '{bc_id}' not found.")
            constraints.append(all_bcs[bc_id])
        study_data.delete_constraints(constraints)

        return command_succeeded("Binding constraints successfully removed.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS.value,
            args={"ids": self.ids},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
