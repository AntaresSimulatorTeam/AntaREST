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

from typing_extensions import override

from antarest.core.exceptions import CandidateNotFoundError
from antarest.study.business.model.xpansion_model import XpansionCandidate
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyXpansionDao(XpansionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        file_study = self.get_file_study()
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        return [XpansionCandidate(**c) for c in candidates.values()]

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        file_study = self.get_file_study()
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        try:
            candidate = next(c for c in candidates.values() if c["name"] == candidate_id)
            return XpansionCandidate(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(f"The candidate '{candidate_id}' does not exist")

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate) -> None:
        raise NotImplementedError()
