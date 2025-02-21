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
import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import field_validator
from typing_extensions import override

from antarest.core.exceptions import CandidateNameIsEmpty, CandidateNotFoundError, IllegalCharacterInNameError
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    assert_xpansion_candidate_name_is_not_already_taken,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


def validate_candidate_name(name: str) -> str:
    # The name is written directly inside the ini file so a specific check is performed here
    if name.strip() == "":
        raise CandidateNameIsEmpty()

    illegal_name_characters = [" ", "\n", "\t", "\r", "\f", "\v", "-", "+", "=", ":", "[", "]", "(", ")"]
    for char in name:
        if char in illegal_name_characters:
            raise IllegalCharacterInNameError(f"The character '{char}' is not allowed in the candidate name")

    return name


class RenameXpansionCandidate(ICommand):
    """
    Command used to rename a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.RENAME_XPANSION_CANDIDATE

    old_name: str
    new_name: str

    @field_validator("old_name", "new_name", mode="before")
    def validate_name(cls, name: str) -> str:
        return validate_candidate_name(name)

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidates = study_data.tree.get(["user", "expansion", "candidates"])

        assert_xpansion_candidate_name_is_not_already_taken(candidates, self.new_name)

        for candidate_id, candidate in candidates.items():
            if candidate["name"] == self.old_name:
                candidates[candidate_id]["name"] = self.new_name
                study_data.tree.save(candidates, ["user", "expansion", "candidates"])

                return self._apply_config(study_data.config)[0]

        raise CandidateNotFoundError(f"The candidate '{self.old_name}' does not exist")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"old_name": self.old_name, "new_name": self.new_name},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
