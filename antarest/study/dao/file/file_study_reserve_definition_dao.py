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

from typing_extensions import override

from antarest.core.exceptions import (
    ChildNotFoundError,
    ReserveDefinitionNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinition
from antarest.study.dao.api.reserve_definition_dao import ReserveDefinitionDao
from antarest.study.dao.common import AreaId, ReserveDefinitionId, ReserveDefinitionsMapping
from antarest.study.dao.file.common import check_area_exists
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_definition import (
    parse_reserve_definition,
    serialize_reserve_definition,
)
from antarest.study.storage.rawstudy.model.filesystem.config.reserves_global_parameters import (
    GLOBAL_PARAMETERS_SECTION,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

_ALL_RESERVES_PATH = ["input", "reserves"]


def _area_reserves_path(area_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves"]


def _reserve_section_path(area_id: str, reserve_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves", reserve_id]


def _is_global_parameters_key(key: str) -> bool:
    return key.lower() == GLOBAL_PARAMETERS_SECTION


def _sections_from_ini(data: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        section_name: section_data  # type: ignore[misc]
        for section_name, section_data in data.items()
        if not _is_global_parameters_key(section_name)
    }


def _parse_reserve_sections(sections: dict[str, dict[str, object]]) -> list[ReserveDefinition]:
    reserves: list[ReserveDefinition] = []
    for section_name, section_data in sections.items():
        merged = dict(section_data)
        merged.setdefault("name", section_name)
        reserves.append(parse_reserve_definition(merged))
    return reserves


class FileStudyReserveDefinitionDao(ReserveDefinitionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    def _read_area_reserves(self, area_id: str) -> dict[str, dict[str, object]]:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)
        try:
            data = file_study.tree.get(_area_reserves_path(area_id))
        except (ChildNotFoundError, KeyError):
            return {}
        return _sections_from_ini(data)

    @override
    def get_all_reserve_definitions(self) -> ReserveDefinitionsMapping:
        file_study = self.get_file_study()
        try:
            data = file_study.tree.get(_ALL_RESERVES_PATH, depth=4)
        except (ChildNotFoundError, KeyError):
            return {}
        result: ReserveDefinitionsMapping = {}
        for area_id, area_data in data.items():
            reserves_data = area_data.get("reserves", {}) if isinstance(area_data, dict) else {}
            reserves = _parse_reserve_sections(_sections_from_ini(reserves_data))
            if reserves:
                result[area_id] = {reserve.id: reserve for reserve in reserves}
        return result

    @override
    def get_all_reserve_definitions_for_area(self, area_id: str) -> Sequence[ReserveDefinition]:
        return _parse_reserve_sections(self._read_area_reserves(area_id))

    @override
    def get_reserve_definition(self, area_id: str, reserve_id: str) -> ReserveDefinition:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)
        try:
            section_data = file_study.tree.get(_reserve_section_path(area_id, reserve_id), depth=1)
        except (ChildNotFoundError, KeyError) as exc:
            raise ReserveDefinitionNotFound(area_id, reserve_id) from exc
        if not isinstance(section_data, dict) or not section_data:
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        merged = dict(section_data)
        merged.setdefault("name", reserve_id)
        return parse_reserve_definition(merged)

    @override
    def reserve_definition_exists(self, area_id: str, reserve_id: str) -> bool:
        file_study = self.get_file_study()
        if area_id not in file_study.config.areas:
            return False
        try:
            section_data = file_study.tree.get(_reserve_section_path(area_id, reserve_id), depth=1)
        except (ChildNotFoundError, KeyError):
            return False
        return bool(section_data)

    @override
    def save_reserve_definitions(self, data: dict[AreaId, list[ReserveDefinition]]) -> None:
        file_study = self.get_file_study()
        for area_id, reserves in data.items():
            check_area_exists(file_study.config, area_id)
            for reserve in reserves:
                section_data = serialize_reserve_definition(reserve)
                file_study.tree.save(section_data, _reserve_section_path(area_id, reserve.id))

    @override
    def delete_reserve_definition(self, area_id: AreaId, reserve_id: ReserveDefinitionId) -> None:
        file_study = self.get_file_study()
        if not self.reserve_definition_exists(area_id, reserve_id):
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        file_study.tree.delete(_reserve_section_path(area_id, reserve_id))
