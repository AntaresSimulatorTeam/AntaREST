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

from pydantic import Field
from typing_extensions import override

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

# minimum required version.
REQUIRED_VERSION = STUDY_VERSION_9_2


class RemoveMultipleSTStorageConstraints(ICommand):
    """
    Command used to remove several short-term storage additional constraints from an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_MULTIPLE_ST_STORAGE_ADDITIONAL_CONSTRAINTS

    # Command parameters
    # ==================

    area_id: str = Field(description="Area ID", pattern=r"[a-z0-9_(),& -]+")
    ids: list[str]

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        existing_constraints = study_data.get_st_storage_additional_constraints_for_area(self.area_id)
        existing_ids = {c.id for c in existing_constraints}
        for constraint_id in self.ids:
            if constraint_id not in existing_ids:
                return command_failed(f"Short-term storage constraint '{constraint_id}' not found.")

        study_data.delete_storage_additional_constraints(self.area_id, self.ids)
        return command_succeeded("Short-term storage constraints successfully removed.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "storage_id": self.storage_id},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
