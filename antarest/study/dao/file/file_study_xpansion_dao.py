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

from antarest.study.business.model.xpansion_model import XpansionCandidate
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyXpansionDao(XpansionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        raise NotImplementedError()

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        raise NotImplementedError()

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate) -> None:
        raise NotImplementedError()
