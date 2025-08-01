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

from typing import List, Optional, cast

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
    is_url_writeable,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveUserResourceData(AntaresBaseModel):
    path: str


class RemoveUserResource(ICommand):
    """
    Command used to delete a resource inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_USER_RESOURCE

    # Command parameters
    # ==================

    data: RemoveUserResourceData

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        url = [item for item in self.data.path.split("/") if item]
        study_tree = study_data.tree
        user_node = cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            return command_failed(message=f"you are not allowed to delete this resource : {self.data.path}")

        try:
            user_node.delete(url)
        except ChildNotFoundError:
            return command_failed(message="the given path doesn't exist")

        return command_succeeded(message=f"Resource {self.data.path} removed successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"data": self.data.model_dump(mode="json")},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
