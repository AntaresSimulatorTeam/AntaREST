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
from typing import Optional

from antarest.study.business.model.xpansion_model import XpansionCandidate, XpansionSettings, XpansionSettingsUpdate


class ReadOnlyXpansionDao(ABC):
    @abstractmethod
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        raise NotImplementedError()

    @abstractmethod
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        raise NotImplementedError()

    @abstractmethod
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        raise NotImplementedError()

    @abstractmethod
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_xpansion_settings(self) -> XpansionSettings:
        raise NotImplementedError()

    @abstractmethod
    def checks_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        raise NotImplementedError()


class XpansionDao(ReadOnlyXpansionDao):
    @abstractmethod
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: Optional[str] = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        raise NotImplementedError()
