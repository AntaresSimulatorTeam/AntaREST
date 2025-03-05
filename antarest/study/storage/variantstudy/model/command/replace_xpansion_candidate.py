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

from antarest.core.exceptions import CandidateAlreadyExistsError, CandidateNotFoundError
from antarest.study.business.model.xpansion_model import XpansionCandidate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.xpansion_common import (
    assert_candidate_is_correct,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceXpansionCandidate(ICommand):
    """
    Command used to replace an existing xpansion candidate with a new one
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_XPANSION_CANDIDATE

    # Command parameters
    # ==================

    candidate_name: str
    new_properties: XpansionCandidate

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Checks candidate validity
        assert_candidate_is_correct(study_data, self.new_properties)
        candidates = study_data.tree.get(["user", "expansion", "candidates"])
        candidates_dict = {}
        candidate_number = None
        for cdt_number, cdt in candidates.items():
            candidate = XpansionCandidate.model_validate(cdt)
            if candidate.name == self.candidate_name:
                candidate_number = cdt_number
            candidates_dict[candidate.name] = candidate

        if candidate_number is None:
            raise CandidateNotFoundError(f"The candidate '{self.candidate_name}' does not exist")

        if self.new_properties.name != self.candidate_name:
            if self.new_properties.name in candidates_dict:
                raise CandidateAlreadyExistsError(f"The candidate '{self.new_properties.name}' already exists")

        candidates[candidate_number] = self.new_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
        study_data.tree.save(candidates, ["user", "expansion", "candidates"])

        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "candidate_name": self.candidate_name,
                "new_properties": self.new_properties.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
