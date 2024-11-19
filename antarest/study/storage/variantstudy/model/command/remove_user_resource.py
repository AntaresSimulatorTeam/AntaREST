# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.serialization import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, is_url_writeable
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveUserResourceData(AntaresBaseModel):
    path: str


class RemoveUserResource(ICommand, RemoveUserResourceData):
    """
    Command used to delete a resource inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_USER_RESOURCE
    version: int = 1

    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        return CommandOutput(status=True, message="ok"), {}

    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        url = [item for item in self.path.split("/") if item]
        study_tree = study_data.tree
        user_node = t.cast(User, study_tree.get_node(["user"]))
        if not is_url_writeable(user_node, url):
            return CommandOutput(status=False, message=f"you are not allowed to delete this resource : {self.path}")

        try:
            user_node.delete(url)
        except ChildNotFoundError:
            return CommandOutput(status=False, message="the given path doesn't exist")

        return CommandOutput(status=True, message="ok")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={"path": self.path}, study_version=self.study_version)

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.path)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveUserResource):
            return False
        return self.path == other.path

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> t.List[str]:
        return []
