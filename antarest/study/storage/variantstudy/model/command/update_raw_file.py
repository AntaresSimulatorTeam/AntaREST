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

import base64
from typing import List, Optional

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateRawFile(ICommand):
    """
    Command used to update a raw file.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_FILE

    # Command parameters
    # ==================

    target: str
    b64Data: str

    @override
    def __repr__(self) -> str:
        cls = self.__class__.__name__
        target = self.target
        try:
            data = base64.decodebytes(self.b64Data.encode("utf-8")).decode("utf-8")
            return f"{cls}(target={target!r}, data={data!r})"
        except (ValueError, TypeError):
            return f"{cls}(target={target!r}, b64Data={self.b64Data!r})"

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, RawFileNode):
            return command_failed(message=f"Study node at path {self.target} is invalid")

        study_data.tree.save(base64.decodebytes(self.b64Data.encode("utf-8")), url)
        return command_succeeded(message=f"File {self.target} updated successfully", should_invalidate_cache=True)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"target": self.target, "b64Data": self.b64Data},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
