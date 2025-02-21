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

from typing_extensions import override

from antarest.core.exceptions import LinkNotFound, XpansionFileNotFoundError
from antarest.study.business.xpansion_management import XpansionCandidateDTO
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


def _assert_link_profile_are_files(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateDTO) -> None:
    existing_files = file_study.tree.get(["user", "expansion", "capa"])
    for attr in [
        "link_profile",
        "already_installed_link_profile",
        "direct_link_profile",
        "indirect_link_profile",
        "already_installed_direct_link_profile",
        "already_installed_indirect_link_profile",
    ]:
        if link_file := getattr(xpansion_candidate_dto, attr, None):
            if link_file not in existing_files:
                raise XpansionFileNotFoundError(f"The '{attr}' file '{link_file}' does not exist")


def _assert_link_exist(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateDTO) -> None:
    area1, area2 = xpansion_candidate_dto.link.split(" - ")
    area_from, area_to = sorted([area1, area2])
    if area_to not in file_study.config.get_links(area_from):
        raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")


def _assert_candidate_is_correct(
    existing_candidates: dict[str, Any], file_study: FileStudy, candidate: XpansionCandidateDTO
) -> None:
    logger.info("Checking given candidate is correct")
    assert_xpansion_candidate_name_is_not_already_taken(existing_candidates, candidate.name)
    _assert_link_profile_are_files(file_study, candidate)
    _assert_link_exist(file_study, candidate)


class CreateXpansionCandidate(ICommand):
    """
    Command used to create a xpansion candidate
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_XPANSION_CANDIDATE

    candidate: XpansionCandidateDTO

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        candidates_obj = study_data.tree.get(["user", "expansion", "candidates"])

        # Checks candidate validity
        _assert_candidate_is_correct(candidates_obj, study_data, self.candidate)

        new_id = str(len(candidates_obj))
        candidates_obj[new_id] = self.candidate.model_dump(mode="json", by_alias=True, exclude_none=True)
        candidates_data = {"user": {"expansion": {"candidates": candidates_obj}}}
        study_data.tree.save(candidates_data)

        return self._apply_config(study_data.config)[0]

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args=self.candidate.model_dump(mode="json", exclude_unset=True),
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
