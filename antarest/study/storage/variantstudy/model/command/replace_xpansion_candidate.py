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
from typing import List, Optional

from typing_extensions import override

from antarest.study.business.model.xpansion_model import (
    XpansionCandidateCreation,
    create_xpansion_candidate,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
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
    properties: XpansionCandidateCreation

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidate = create_xpansion_candidate(self.properties)
        candidates = study_data.get_all_xpansion_candidates()

        # Checks candidate validity
        existing_ids = {cdt.name for cdt in candidates}
        if self.candidate_name not in existing_ids:
            return command_failed(f"The candidate '{candidate.name}' does not exist")
        study_data.checks_xpansion_candidate_coherence(candidate)

        old_name = None
        if self.properties.name != self.candidate_name:
            # We're renaming the candidate
            old_name = self.candidate_name
            if self.properties.name in existing_ids:
                return command_failed(f"The candidate '{self.properties.name}' already exists")

        study_data.save_xpansion_candidate(candidate, old_name)
        return command_succeeded(message=f"Candidate {self.candidate_name} replaced successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "candidate_name": self.candidate_name,
                "properties": self.properties.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
