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

import base64
from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateRawFile(ICommand):
    """
    Command used to update a raw file.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_FILE
    version: int = 1

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
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, RawFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(base64.decodebytes(self.b64Data.encode("utf-8")), url)
        return CommandOutput(status=True, message="ok")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"target": self.target, "b64Data": self.b64Data},
            study_version=self.study_version,
        )

    @override
    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target)

    @override
    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateRawFile):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.b64Data == other.b64Data

    @override
    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    @override
    def get_inner_matrices(self) -> List[str]:
        return []

    @override
    def can_update_study_config(self) -> bool:
        return False
