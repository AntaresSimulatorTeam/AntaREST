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

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)
from antarest.study.dao.common import (
    AreaId,
    ThermalClusterReserveParticipationsMapping,
    ThermalId,
)


class ReadOnlyThermalClusterReserveParticipationDao(ABC):
    @abstractmethod
    def get_all_thermal_cluster_reserve_participations(self) -> ThermalClusterReserveParticipationsMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermal_cluster_reserve_participations_for_cluster(
        self, area_id: str, thermal_id: str
    ) -> Sequence[ThermalClusterReserveParticipation]:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_cluster_reserve_participation(
        self, area_id: str, thermal_id: str, reserve_id: str
    ) -> ThermalClusterReserveParticipation:
        raise NotImplementedError()

    @abstractmethod
    def thermal_cluster_reserve_participation_exists(self, area_id: str, thermal_id: str, reserve_id: str) -> bool:
        raise NotImplementedError()


class ThermalClusterReserveParticipationDao(ReadOnlyThermalClusterReserveParticipationDao):
    @abstractmethod
    def save_thermal_cluster_reserve_participations(
        self,
        data: dict[AreaId, dict[ThermalId, list[ThermalClusterReserveParticipation]]],
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_thermal_cluster_reserve_participations(
        self,
        area_id: AreaId,
        thermal_id: ThermalId,
        reserve_ids: Sequence[ReserveDefinitionId],
    ) -> None:
        raise NotImplementedError()
