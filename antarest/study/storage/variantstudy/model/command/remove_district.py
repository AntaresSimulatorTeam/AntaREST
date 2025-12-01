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

from typing import Optional

from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveDistrict(ICommand):
    """
    Command used to remove a district from the study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_DISTRICT

    # Command parameters
    # ==================

    id: str

    def remove_from_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        del study_data.districts[self.id]
        return command_succeeded(message=self.id)

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.district_exists(self.id):
            return command_failed(message=f"District '{self.id}' does not exist and should be created")
        study_data.remove_district(self.id)
        return command_succeeded(message=self.id)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args={
                "id": self.id,
            },
            study_version=self.study_version,
        )
