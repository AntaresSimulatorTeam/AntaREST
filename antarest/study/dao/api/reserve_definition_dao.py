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
from collections.abc import Sequence

import polars as pl

from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveDefinitionId
from antarest.study.dao.common import AreaId, ReserveDefinitionsMapping, ReserveNeedsMapping


class ReadOnlyReserveDefinitionDao(ABC):
    @abstractmethod
    def get_all_reserve_definitions(self) -> ReserveDefinitionsMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_reserve_definitions_for_area(self, area_id: str) -> Sequence[ReserveDefinition]:
        raise NotImplementedError()

    @abstractmethod
    def get_reserve_definition(self, area_id: str, reserve_id: str) -> ReserveDefinition:
        raise NotImplementedError()

    @abstractmethod
    def reserve_definition_exists(self, area_id: str, reserve_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_reserve_need(self, area_id: str, reserve_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_all_reserve_needs(self) -> ReserveNeedsMapping:
        raise NotImplementedError()


class ReserveDefinitionDao(ReadOnlyReserveDefinitionDao):
    @abstractmethod
    def save_reserve_definitions(self, data: dict[AreaId, list[ReserveDefinition]]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_reserve_definitions(self, area_id: AreaId, reserve_ids: Sequence[ReserveDefinitionId]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_reserve_needs(self, mapping: ReserveNeedsMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_reserve_need(self, area_id: AreaId, reserve_id: ReserveDefinitionId) -> None:
        raise NotImplementedError()
