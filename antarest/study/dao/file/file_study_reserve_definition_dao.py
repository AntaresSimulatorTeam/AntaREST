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
from typing import TYPE_CHECKING, Any

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import (
    ChildNotFoundError,
    ReserveDefinitionNotFound,
)
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionId,
)
from antarest.study.dao.api.reserve_definition_dao import ReserveDefinitionDao
from antarest.study.dao.common import AreaId, ReserveDefinitionsMapping, ReserveNeedsMapping
from antarest.study.dao.file.common import check_area_exists
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_definition import (
    parse_reserve_definition,
    serialize_reserve_definitions,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _area_reserves_path(area_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves", "reserves"]


def _reserve_section_path(area_id: str, reserve_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves", reserve_id]


def _reserve_need_matrix_path(area_id: AreaId, reserve_id: ReserveDefinitionId) -> list[str]:
    return ["input", "reserves", area_id, reserve_id]


class FileStudyReserveDefinitionDao(ReserveDefinitionDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    def _read_area_reserves(self, area_id: str) -> list[dict[str, Any]]:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)
        try:
            data = file_study.tree.get(_area_reserves_path(area_id))
        except (ChildNotFoundError, KeyError):
            return []
        return data

    @override
    def get_all_reserve_definitions(self) -> ReserveDefinitionsMapping:
        file_study = self.get_file_study()
        result: ReserveDefinitionsMapping = {}
        for area_id in file_study.config.areas:
            reserves = self.get_all_reserve_definitions_for_area(area_id)
            if reserves:
                result[area_id] = {ReserveDefinitionId(reserve.id): reserve for reserve in reserves}
        return result

    @override
    def get_all_reserve_definitions_for_area(self, area_id: str) -> Sequence[ReserveDefinition]:
        all_area_reserves = self._read_area_reserves(area_id)
        return [parse_reserve_definition(reserves) for reserves in all_area_reserves]

    @override
    def get_reserve_definition(self, area_id: str, reserve_id: str) -> ReserveDefinition:
        all_area_reserves = self.get_all_reserve_definitions_for_area(area_id)
        for reserve in all_area_reserves:
            if reserve.id == reserve_id:
                return reserve
        raise ReserveDefinitionNotFound(area_id, reserve_id)

    @override
    def reserve_definition_exists(self, area_id: str, reserve_id: str) -> bool:
        return reserve_id in self.get_file_study().config.areas[area_id].reserves

    @override
    def save_reserve_definitions(self, data: dict[AreaId, list[ReserveDefinition]]) -> None:
        file_study = self.get_file_study()
        for area_id, reserves in data.items():
            existing_reserves = self.get_all_reserve_definitions_for_area(area_id)
            reserves_to_update = {r.id: r for r in reserves}

            new_reserves = []
            for reserve in existing_reserves:
                if reserve.id not in reserves_to_update:
                    new_reserves.append(reserve)
                else:
                    new_reserves.append(reserves_to_update.pop(reserve.id))

            # Update the files
            file_study.tree.save(serialize_reserve_definitions(new_reserves), _area_reserves_path(area_id))

            # Update the config
            for reserve in reserves:
                if reserve.id not in file_study.config.areas[area_id].reserves:
                    file_study.config.areas[area_id].reserves.append(reserve.id)

    @override
    def delete_reserve_definitions(self, area_id: AreaId, reserve_ids: Sequence[ReserveDefinitionId]) -> None:
        file_study = self.get_file_study()

        # Check that the given ids exist
        for reserve_id in reserve_ids:
            if not self.reserve_definition_exists(area_id, reserve_id):
                raise ReserveDefinitionNotFound(area_id, reserve_id)

        # Remove data from the YAML file
        all_reserves = self.get_all_reserve_definitions_for_area(area_id)
        new_reserves = []
        ids_to_remove = set(reserve_ids)
        for reserve in all_reserves:
            if reserve.id not in ids_to_remove:
                new_reserves.append(reserve)
        file_study.tree.save(serialize_reserve_definitions(new_reserves), _area_reserves_path(area_id))

        # Remove the matrices
        for reserve_id in reserve_ids:
            file_study.tree.delete(_reserve_need_matrix_path(area_id, reserve_id))

        # Keep config in sync — remove deleted reserves from the area's list.
        area_config = file_study.config.areas[area_id]
        area_config.reserves = [rid for rid in area_config.reserves if rid not in reserve_ids]

    @override
    def get_reserve_need(self, area_id: str, reserve_id: str) -> pl.DataFrame:
        if not self.reserve_definition_exists(area_id, reserve_id):
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        return self.get_impl().get_matrix(_reserve_need_matrix_path(area_id, ReserveDefinitionId(reserve_id)))

    @override
    def get_all_reserve_needs(self) -> ReserveNeedsMapping:
        study_data = self.get_file_study()
        matrix_nodes: dict[InputSeriesMatrix, tuple[str, ReserveDefinitionId]] = {}
        for area_id, area in study_data.config.areas.items():
            for reserve_id in area.reserves:
                url = _reserve_need_matrix_path(area_id, ReserveDefinitionId(reserve_id))
                node = study_data.tree.get_node(url)
                assert isinstance(node, InputSeriesMatrix)
                matrix_nodes[node] = (area_id, ReserveDefinitionId(reserve_id))

        result: ReserveNeedsMapping = {}
        matrices_mapping = self.get_impl().get_matrices_ids(list(matrix_nodes))
        for node, matrix_id in matrices_mapping.items():
            area_id, reserve_id = matrix_nodes[node]
            result.setdefault(area_id, {})[reserve_id] = matrix_id
        return result

    @override
    def save_reserve_needs(self, mapping: ReserveNeedsMapping) -> None:
        study_data = self.get_file_study()
        matrices_mapping: dict[str, list[InputSeriesMatrix]] = {}
        for area_id, per_reserve in mapping.items():
            for reserve_id, series_id in per_reserve.items():
                url = _reserve_need_matrix_path(area_id, reserve_id)
                node = study_data.tree.get_node(url)
                assert isinstance(node, InputSeriesMatrix)
                matrices_mapping.setdefault(series_id, []).append(node)
        self.get_impl().save_matrices(matrices_mapping)
