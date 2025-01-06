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

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveDistrict(ICommand):
    """
    Command used to remove a district from the study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_DISTRICT
    version: int = 1

    # Command parameters
    # ==================

    id: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        del study_data.sets[self.id]
        return CommandOutput(status=True, message=self.id), dict()

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        output, _ = self._apply_config(study_data.config)
        study_data.tree.delete(["input", "areas", "sets", self.id])
        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args={
                "id": self.id,
            },
            study_version=self.study_version,
        )

    @override
    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    @override
    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveDistrict):
            return False
        return self.id == other.id

    @override
    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    @override
    def get_inner_matrices(self) -> List[str]:
        return []

    @override
    def can_update_study_config(self) -> bool:
        return True
