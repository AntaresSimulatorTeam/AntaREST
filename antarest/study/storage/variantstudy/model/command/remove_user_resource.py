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
from pathlib import PurePosixPath
from typing import Optional

from typing_extensions import override

from antarest.study.business.model.user_model import UserResourceDataRemoval
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveUserResource(ICommand):
    """
    Command used to delete a resource inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_USER_RESOURCE

    # Command parameters
    # ==================

    data: UserResourceDataRemoval

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        resource_path = PurePosixPath(self.data.path)
        study_data.delete_user_resource(resource_path)
        return command_succeeded(message=f"Resource {resource_path} removed successfully.", result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"data": self.data.model_dump(mode="json")},
            study_version=self.study_version,
        )
