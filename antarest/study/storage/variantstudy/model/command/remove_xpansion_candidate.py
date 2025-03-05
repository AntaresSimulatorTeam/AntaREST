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
from antarest.study.business.model.xpansion_model import XpansionCandidate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveXpansionCandidate(ICommand):
    """
    Command used to delete a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_XPANSION_CANDIDATE

    # Command parameters
    # ==================

    candidate_name: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidates = study_data.tree.get(["user", "expansion", "candidates"])
        candidate_number = None
        for cdt_number, cdt in candidates.items():
            candidate = XpansionCandidate.model_validate(cdt)
            if candidate.name == self.candidate_name:
                candidate_number = cdt_number

        if not candidate_number:
            raise CandidateNotFoundError(f"The candidate '{self.candidate_name}' does not exist")

        del candidates[candidate_number]
        # Reorder keys of the dict
        new_dict = {str(i): v for i, (k, v) in enumerate(candidates.items(), 1)}

        study_data.tree.save(data=new_dict, url=["user", "expansion", "candidates"])

        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"candidate_name": self.candidate_name},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
