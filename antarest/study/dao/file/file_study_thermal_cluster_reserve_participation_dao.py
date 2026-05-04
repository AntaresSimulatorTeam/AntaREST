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
from typing import Any

from typing_extensions import override

from antarest.core.exceptions import (
    ChildNotFoundError,
    ThermalClusterReserveParticipationNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)
from antarest.study.dao.api.thermal_cluster_reserve_participation_dao import (
    ThermalClusterReserveParticipationDao,
)
from antarest.study.dao.common import AreaId, ThermalClusterReserveParticipationsMapping, ThermalId
from antarest.study.dao.file.common import check_area_exists
from antarest.study.storage.rawstudy.model.filesystem.config.thermal_cluster_reserve_participation import (
    extract_reserve_id,
    parse_thermal_cluster_reserve_participation,
    section_name,
    serialize_thermal_cluster_reserve_participation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _reserves_path(area_id: str) -> list[str]:
    return ["input", "thermal", "clusters", area_id, "reserves"]


def _section_key_for(thermal_id: str, sections: dict[str, dict[str, Any]], reserve_id: str) -> str | None:
    """Find the actual section key used to store ``(thermal_id, reserve_id)``.

    The composite section name follows ``<thermal_id>__<reserve_id>``. Because both
    parts can contain the separator string, the section is identified by:
    1. starting with ``<thermal_id>__`` and
    2. having a ``cluster-name`` content field equal to ``thermal_id`` and a derived
       ``reserve_id`` equal to the queried one.
    """
    for raw_key, raw_data in sections.items():
        cluster_name = raw_data.get("cluster-name") if isinstance(raw_data, dict) else None
        if cluster_name != thermal_id:
            continue
        derived = extract_reserve_id(raw_key, thermal_id)
        if derived == reserve_id:
            return raw_key
    return None


class FileStudyThermalClusterReserveParticipationDao(ThermalClusterReserveParticipationDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    def _read_area_participations(self, area_id: str) -> dict[str, dict[str, Any]]:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)
        try:
            data = file_study.tree.get(_reserves_path(area_id))
        except (ChildNotFoundError, KeyError):
            return {}
        return data

    @override
    def get_all_thermal_cluster_reserve_participations(self) -> ThermalClusterReserveParticipationsMapping:
        file_study = self.get_file_study()
        result: ThermalClusterReserveParticipationsMapping = {}
        for area_id in file_study.config.areas:
            participations = self._participations_by_cluster(area_id)
            if participations:
                result[area_id] = participations
        return result

    @override
    def get_all_thermal_cluster_reserve_participations_for_cluster(
        self, area_id: str, thermal_id: str
    ) -> Sequence[ThermalClusterReserveParticipation]:
        check_area_exists(self.get_file_study().config, area_id)
        return list(self._participations_by_cluster(area_id).get(thermal_id, {}).values())

    @override
    def get_thermal_cluster_reserve_participation(
        self, area_id: str, thermal_id: str, reserve_id: str
    ) -> ThermalClusterReserveParticipation:
        sections = self._read_area_participations(area_id)
        key = _section_key_for(thermal_id, sections, reserve_id)
        if key is None:
            raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, reserve_id)
        return parse_thermal_cluster_reserve_participation(reserve_id, sections[key])

    @override
    def thermal_cluster_reserve_participation_exists(self, area_id: str, thermal_id: str, reserve_id: str) -> bool:
        file_study = self.get_file_study()
        if area_id not in file_study.config.areas:
            return False
        sections = self._read_area_participations(area_id)
        return _section_key_for(thermal_id, sections, reserve_id) is not None

    @override
    def save_thermal_cluster_reserve_participations(
        self,
        data: dict[AreaId, dict[ThermalId, list[ThermalClusterReserveParticipation]]],
    ) -> None:
        file_study = self.get_file_study()
        for area_id, by_cluster in data.items():
            check_area_exists(file_study.config, area_id)
            try:
                existing = file_study.tree.get(_reserves_path(area_id))
            except (ChildNotFoundError, KeyError):
                existing = {}
            for thermal_id, participations in by_cluster.items():
                for participation in participations:
                    # Drop any pre-existing section that maps to the same (cluster, reserve)
                    # — this guards against a stale section under a different composite
                    # key (e.g. when the cluster_name was changed elsewhere).
                    stale_key = _section_key_for(thermal_id, existing, participation.id)
                    if stale_key is not None:
                        existing.pop(stale_key)
                    existing[section_name(thermal_id, participation.id)] = (
                        serialize_thermal_cluster_reserve_participation(thermal_id, participation)
                    )
            file_study.tree.save(existing, _reserves_path(area_id))

    @override
    def delete_thermal_cluster_reserve_participations(
        self,
        area_id: AreaId,
        thermal_id: ThermalId,
        reserve_ids: Sequence[ReserveDefinitionId],
    ) -> None:
        sections = self._read_area_participations(area_id)
        keys_to_remove: list[str] = []
        for rid in reserve_ids:
            key = _section_key_for(thermal_id, sections, rid)
            if key is None:
                raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, rid)
            keys_to_remove.append(key)
        for key in keys_to_remove:
            sections.pop(key, None)
        self.get_file_study().tree.save(sections, _reserves_path(area_id))

    def _participations_by_cluster(
        self, area_id: str
    ) -> dict[str, dict[ReserveDefinitionId, ThermalClusterReserveParticipation]]:
        sections = self._read_area_participations(area_id)
        result: dict[str, dict[ReserveDefinitionId, ThermalClusterReserveParticipation]] = {}
        for raw_key, raw_data in sections.items():
            if not isinstance(raw_data, dict):
                continue
            cluster_name = raw_data.get("cluster-name")
            if not isinstance(cluster_name, str):
                continue
            reserve_id = extract_reserve_id(raw_key, cluster_name)
            if reserve_id is None:
                continue
            participation = parse_thermal_cluster_reserve_participation(reserve_id, raw_data)
            result.setdefault(cluster_name, {})[ReserveDefinitionId(reserve_id)] = participation
        return result
