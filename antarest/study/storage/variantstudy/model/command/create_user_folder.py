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
from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateUserFolder(ICommand):
    """
    Command used to create a folder inside the `user` folder.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_USER_FOLDER
    version: int = 1

    # Command parameters
    # ==================

    path: str

    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        return CommandOutput(status=True, message="ok"), {}

    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        url = [item for item in self.path.split("/") if item]
        if len(url) < 2 or url[0] != "user":
            return CommandOutput(status=False, message=f"the given path isn't inside the 'User' folder: {self.path}")
        if url[1] == "expansion":
            return CommandOutput(
                status=False, message=f"the given path shouldn't be inside the 'expansion' folder: {self.path}"
            )

        study_tree = study_data.tree
        try:
            study_tree.get_node(url)
        except ChildNotFoundError:
            # Creates the tree recursively to be able to create a folder inside a non-existing one.
            result: JSON = {}
            current = result
            for key in url:
                current[key] = {}
                current = current[key]
            study_data.tree.save(result)
        else:
            return CommandOutput(status=False, message=f"the given folder already exists: {self.path}")
        return CommandOutput(status=True, message="ok")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={"path": str(self.path)})

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + str(self.path))

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateUserFolder):
            return False
        return self.path == other.path

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> t.List[str]:
        return []
