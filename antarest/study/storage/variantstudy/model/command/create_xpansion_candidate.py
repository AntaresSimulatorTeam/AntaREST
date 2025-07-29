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


class CreateXpansionCandidate(ICommand):
    """
    Command used to create a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_XPANSION_CANDIDATE

    # Command parameters
    # ==================

    candidate: XpansionCandidateCreation

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidate = create_xpansion_candidate(self.candidate)
        candidates = study_data.get_all_xpansion_candidates()

        # Checks candidate validity
        for cdt in candidates:
            if cdt.name == candidate.name:
                return command_failed(f"The candidate '{candidate.name}' already exists")
        study_data.checks_xpansion_candidate_coherence(candidate)

        study_data.save_xpansion_candidate(candidate)
        return command_succeeded(message=f"Candidate {self.candidate.name} created successfully")

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
