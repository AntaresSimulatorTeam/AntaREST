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
    ReserveDefinitionNotFound,
)
from antarest.study.business.model.reserve_definition_model import (
    GLOBAL_PARAMETERS_SECTION,
    ReserveDefinition,
    ReserveDefinitionId,
)
from antarest.study.dao.api.reserve_definition_dao import ReserveDefinitionDao
from antarest.study.dao.common import AreaId, ReserveDefinitionsMapping
from antarest.study.dao.file.common import check_area_exists
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_definition import (
    parse_reserve_definition,
    serialize_reserve_definition,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _area_reserves_path(area_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves"]


def _reserve_section_path(area_id: str, reserve_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves", reserve_id]


def _is_global_parameters_key(key: str) -> bool:
    return key.lower() == GLOBAL_PARAMETERS_SECTION


def _sections_from_ini(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        section_name: section_data
        for section_name, section_data in data.items()
        if not _is_global_parameters_key(section_name)
    }


def _parse_reserve_sections(sections: dict[str, dict[str, object]]) -> list[ReserveDefinition]:
    return [parse_reserve_definition({"name": name, **data}) for name, data in sections.items()]


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
        result: ReserveDefinitionsMapping = {}
        for area_id in file_study.config.areas:
            reserves = self.get_all_reserve_definitions_for_area(area_id)
            if reserves:
                result[area_id] = {reserve.id: reserve for reserve in reserves}
        return result

    @override
    def get_all_reserve_definitions_for_area(self, area_id: str) -> Sequence[ReserveDefinition]:
        return _parse_reserve_sections(self._read_area_reserves(area_id))

    @override
    def get_reserve_definition(self, area_id: str, reserve_id: str) -> ReserveDefinition:
        sections = self._read_area_reserves(area_id)
        if reserve_id not in sections:
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        return parse_reserve_definition({"name": reserve_id, **sections[reserve_id]})

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
            try:
                existing = file_study.tree.get(_area_reserves_path(area_id))
            except (ChildNotFoundError, KeyError):
                existing = {}
            existing.update({reserve.id: serialize_reserve_definition(reserve) for reserve in reserves})
            file_study.tree.save(existing, _area_reserves_path(area_id))

    @override
    def delete_reserve_definitions(self, area_id: AreaId, reserve_ids: Sequence[ReserveDefinitionId]) -> None:
        file_study = self.get_file_study()
        for reserve_id in reserve_ids:
            if not self.reserve_definition_exists(area_id, reserve_id):
                raise ReserveDefinitionNotFound(area_id, reserve_id)
        for reserve_id in reserve_ids:
            file_study.tree.delete(_reserve_section_path(area_id, reserve_id))
