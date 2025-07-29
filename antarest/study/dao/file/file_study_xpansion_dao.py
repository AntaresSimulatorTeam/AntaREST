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
from abc import ABC, abstractmethod
from typing import Any, Optional

from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    ChildNotFoundError,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionFileNotFoundError,
)
from antarest.study.business.model.xpansion_model import XpansionCandidate
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyXpansionDao(XpansionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        candidates = self._get_all_xpansion_candidates()
        return [XpansionCandidate(**c) for c in candidates.values()]

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        candidates = self._get_all_xpansion_candidates()
        try:
            candidate = next(c for c in candidates.values() if c["name"] == candidate_id)
            return XpansionCandidate(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(f"The candidate '{candidate_id}' does not exist")

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        self._assert_link_profile_are_files(candidate)
        self._assert_link_exist(candidate)

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        file_study = self.get_file_study()
        sensitivity_config = self._get_xpansion_sensitivity(file_study)
        projections = sensitivity_config.get("projection", {})
        if candidate_name in projections:
            raise XpansionCandidateDeletionError(file_study.config.study_id, candidate_name)

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: Optional[str] = None) -> None:
        candidates = self._get_all_xpansion_candidates()
        existing_ids = {value["name"]: key for key, value in candidates.items()}

        if old_id:
            # We should remove the candidate corresponding to the `old_id`
            del candidates[existing_ids[old_id]]

        new_key = existing_ids.get(candidate.name, str(len(candidates) + 1))  # The first candidate key is 1
        candidates[new_key] = candidate.model_dump(mode="json", by_alias=True, exclude_none=True)
        self._save_candidates(candidates)

    @override
    def delete_xpansion_candidate(self, candidate: XpansionCandidate) -> None:
        candidates = self._get_all_xpansion_candidates()
        existing_ids = {value["name"]: key for key, value in candidates.items()}
        del candidates[existing_ids[candidate.name]]
        # Reorder keys of the dict
        new_dict = {str(i): v for i, (k, v) in enumerate(candidates.items(), 1)}
        self._save_candidates(new_dict)

    def _save_candidates(self, content: dict[str, Any]) -> None:
        self.get_file_study().tree.save(content, ["user", "expansion", "candidates"])

    def _get_all_xpansion_candidates(self) -> dict[str, Any]:
        file_study = self.get_file_study()
        return file_study.tree.get(["user", "expansion", "candidates"])

    def _assert_link_profile_are_files(self, xpansion_candidate_dto: XpansionCandidate) -> None:
        file_study = self.get_file_study()
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

    def _assert_link_exist(self, xpansion_candidate_dto: XpansionCandidate) -> None:
        file_study = self.get_file_study()
        area_from = xpansion_candidate_dto.link.area_from
        area_to = xpansion_candidate_dto.link.area_to
        if area_from not in file_study.config.areas:
            raise AreaNotFound(area_from)
        if area_to not in file_study.config.get_links(area_from):
            raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")

    @staticmethod
    def _get_xpansion_sensitivity(file_study: FileStudy) -> dict[str, Any]:
        try:
            return file_study.tree.get(["user", "expansion", "sensitivity", "sensitivity_in"])
        except ChildNotFoundError:
            return {}
