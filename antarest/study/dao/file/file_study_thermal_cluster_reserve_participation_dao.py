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
from typing import Any, cast

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
    parse_thermal_cluster_reserve_participation,
    serialize_thermal_cluster_reserve_participation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _reserves_path(area_id: str) -> list[str]:
    return ["input", "thermal", "clusters", area_id, "reserves"]


SectionEntry = tuple[str, dict[str, Any]]


def _is_participation_section(content: Any, thermal_id: str) -> bool:
    return isinstance(content, dict) and content.get("cluster-name") == thermal_id


class FileStudyThermalClusterReserveParticipationDao(ThermalClusterReserveParticipationDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    def _read_area_participations(self, area_id: str) -> list[SectionEntry]:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)
        try:
            data = file_study.tree.get(_reserves_path(area_id))
        except (ChildNotFoundError, KeyError):
            return []
        return cast(list[SectionEntry], data)

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
        for section_name, content in self._read_area_participations(area_id):
            if section_name == reserve_id and _is_participation_section(content, thermal_id):
                return parse_thermal_cluster_reserve_participation(reserve_id, content)
        raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, reserve_id)

    @override
    def thermal_cluster_reserve_participation_exists(self, area_id: str, thermal_id: str, reserve_id: str) -> bool:
        file_study = self.get_file_study()
        if area_id not in file_study.config.areas:
            return False
        for section_name, content in self._read_area_participations(area_id):
            if section_name == reserve_id and _is_participation_section(content, thermal_id):
                return True
        return False

    @override
    def save_thermal_cluster_reserve_participations(
        self,
        data: dict[AreaId, dict[ThermalId, list[ThermalClusterReserveParticipation]]],
    ) -> None:
        file_study = self.get_file_study()
        for area_id, by_cluster in data.items():
            check_area_exists(file_study.config, area_id)
            sections = self._read_area_participations(area_id)
            # (thermal_id, reserve_id) pairs we are about to (re)write — their existing
            # occurrences must be dropped to avoid duplicates after append.
            replacing: set[tuple[str, str]] = {
                (thermal_id, p.id) for thermal_id, participations in by_cluster.items() for p in participations
            }
            updated: list[SectionEntry] = []
            for section_name, content in sections:
                cluster_name = content.get("cluster-name") if isinstance(content, dict) else None
                if isinstance(cluster_name, str) and (cluster_name, section_name) in replacing:
                    continue
                updated.append((section_name, content))
            for thermal_id, participations in by_cluster.items():
                for p in participations:
                    updated.append((p.id, serialize_thermal_cluster_reserve_participation(thermal_id, p)))
            file_study.tree.save(updated, _reserves_path(area_id))

    @override
    def delete_thermal_cluster_reserve_participations(
        self,
        area_id: AreaId,
        thermal_id: ThermalId,
        reserve_ids: Sequence[ReserveDefinitionId],
    ) -> None:
        sections = self._read_area_participations(area_id)
        targets = set(reserve_ids)
        found = {
            section_name
            for section_name, content in sections
            if section_name in targets and _is_participation_section(content, thermal_id)
        }
        for rid in reserve_ids:
            if rid not in found:
                raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, rid)
        updated: list[SectionEntry] = [
            (section_name, content)
            for section_name, content in sections
            if not (section_name in targets and _is_participation_section(content, thermal_id))
        ]
        self.get_file_study().tree.save(updated, _reserves_path(area_id))

    def _participations_by_cluster(
        self, area_id: str
    ) -> dict[str, dict[ReserveDefinitionId, ThermalClusterReserveParticipation]]:
        sections = self._read_area_participations(area_id)
        result: dict[str, dict[ReserveDefinitionId, ThermalClusterReserveParticipation]] = {}
        for section_name, content in sections:
            if not isinstance(content, dict):
                continue
            cluster_name = content.get("cluster-name")
            if not isinstance(cluster_name, str):
                continue
            participation = parse_thermal_cluster_reserve_participation(section_name, content)
            result.setdefault(cluster_name, {})[ReserveDefinitionId(section_name)] = participation
        return result
