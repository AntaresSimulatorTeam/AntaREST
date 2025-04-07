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

from antarest.core.exceptions import CandidateAlreadyExistsError
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


class CreateXpansionCandidate(ICommand):
    """
    Command used to create a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_XPANSION_CANDIDATE

    # Command parameters
    # ==================

    candidate: XpansionCandidate

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:  # type: ignore
        pass  # TODO DELETE

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidates = study_data.tree.get(["user", "expansion", "candidates"])
        candidates_dict = {}
        for cdt in candidates.values():
            candidate = XpansionCandidate.model_validate(cdt)
            candidates_dict[candidate.name] = candidate

        # Checks candidate validity
        if self.candidate.name in candidates_dict:
            raise CandidateAlreadyExistsError(f"The candidate '{self.candidate.name}' already exists")
        assert_candidate_is_correct(study_data, self.candidate)

        new_id = str(len(candidates) + 1)  # The first candidate key is 1
        candidates[new_id] = self.candidate.model_dump(mode="json", by_alias=True, exclude_none=True)
        candidates_data = {"user": {"expansion": {"candidates": candidates}}}
        study_data.tree.save(candidates_data)

        return CommandOutput(status=True, message="ok")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"candidate": self.candidate.model_dump(mode="json", by_alias=True, exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
