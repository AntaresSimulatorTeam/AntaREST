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
from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.core.exceptions import CandidateNotFoundError
from antarest.study.business.model.xpansion_model import XpansionCandidateInternal
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.xpansion_common import (
    assert_xpansion_candidate_name_is_not_already_taken,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateXpansionCandidate(ICommand):
    """
    Command used to update a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_XPANSION_CANDIDATE

    # Command parameters
    # ==================

    candidate_name: str
    new_properties: XpansionCandidateInternal

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidates = study_data.tree.get(["user", "expansion", "candidates"])

        if self.new_properties.name != self.candidate_name:
            assert_xpansion_candidate_name_is_not_already_taken(candidates, self.new_properties.name)

        for candidate_id, candidate in candidates.items():
            if candidate["name"] == self.candidate_name:
                # NOTE: this behavior is weird, but we have to keep it as is to fit with the existing code
                candidates[candidate_id] = self.new_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                study_data.tree.save(candidates, ["user", "expansion", "candidates"])

                return self._apply_config(study_data.config)[0]

        raise CandidateNotFoundError(f"The candidate '{self.candidate_name}' does not exist")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "candidate_name": self.candidate_name,
                "new_properties": self.new_properties.model_dump(mode="json", by_alias=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
