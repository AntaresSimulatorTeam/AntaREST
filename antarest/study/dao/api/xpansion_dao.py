# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import polars as pl

from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.common import XpansionCapacitiesMapping, XpansionConstraintsMapping, XpansionWeightsMapping


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
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        raise NotImplementedError()

    @abstractmethod
    def get_all_xpansion_weights(self) -> XpansionWeightsMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_xpansion_capacities(self) -> XpansionCapacitiesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_xpansion_constraints(self) -> XpansionConstraintsMapping:
        raise NotImplementedError()


class XpansionDao(ReadOnlyXpansionDao):
    @abstractmethod
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: str | None = None) -> None:
        """
        Upsert a candidate.

        Args:
            candidate: The candidate to create or update.
            old_id: Current candidate name, only provided when renaming a candidate.

        Raises:
            CandidateNotFoundError: If ``old_id`` is provided but does not exist.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_candidates(self, candidates: list[XpansionCandidate]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_xpansion_configuration(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_xpansion_configuration(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_constraint(self, data: XpansionConstraintsMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_capacity(self, data: XpansionCapacitiesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_weight(self, data: XpansionWeightsMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        raise NotImplementedError()
