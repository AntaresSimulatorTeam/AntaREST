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
from enum import StrEnum
from typing import Any, Dict, List, Optional, Tuple, cast

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, is_url_writeable
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"


class CreateUserResourceData(AntaresBaseModel):
    path: str
    resource_type: ResourceType


class CreateUserResource(ICommand):
    """
    Command used to create a resource inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_USER_RESOURCE

    # Command parameters
    # ==================

    data: CreateUserResourceData

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:  # type: ignore
        pass  # TODO DELETE

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        url = [item for item in self.data.path.split("/") if item]
        study_tree = study_data.tree
        user_node = cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            return CommandOutput(
                status=False, message=f"you are not allowed to create a resource here: {self.data.path}"
            )
        try:
            study_tree.get_node(["user"] + url)
        except ChildNotFoundError:
            # Creates the tree recursively to be able to create a resource inside a non-existing folder.
            last_value = b"" if self.data.resource_type == ResourceType.FILE else {}
            nested_dict: JSON = {url[-1]: last_value}
            for key in reversed(url[:-1]):
                nested_dict = {key: nested_dict}
            study_tree.save({"user": nested_dict})
        else:
            return CommandOutput(status=False, message=f"the given resource already exists: {self.data.path}")
        return CommandOutput(status=True, message="ok")

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
