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
from antarest.study.model import STUDY_VERSION_8_6
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
REQUIRED_VERSION = STUDY_VERSION_8_6


class RemoveSTStorage(ICommand):
    """
    Command used to remove a short-term storage from an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_ST_STORAGE

    # Command parameters
    # ==================

    area_id: str = Field(description="Area ID", pattern=r"[a-z0-9_(),& -]+")
    storage_id: str = Field(description="Short term storage ID", pattern=r"[a-z0-9_(),& -]+")

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.st_storage_exists(self.area_id, self.storage_id):
            return command_failed(f"Short-term storage '{self.storage_id}' in area '{self.area_id}' does not exist")

        storage = study_data.get_st_storage(self.area_id, self.storage_id)

        # Checks the storage is not referenced in any constraint
        existing_constraints = study_data.get_st_storage_additional_constraints_for_area(self.area_id)
        for constraint in existing_constraints:
            if constraint.cluster == storage.id:
                return command_failed(
                    f"Short-term storage '{self.storage_id}' is referenced in the constraint '{constraint.id}'."
                )

        study_data.delete_st_storage(self.area_id, storage)

        return command_succeeded(f"Short-term storage '{self.storage_id}' inside area '{self.area_id}' deleted")

    @override
    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "storage_id": self.storage_id},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
