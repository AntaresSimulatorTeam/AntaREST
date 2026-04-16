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
from abc import abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from antarest.core.exceptions import AreaNotFound, ChildNotFoundError
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationMatrix,
)
from antarest.study.dao.common import AreaId, AreaSeriesMapping
from antarest.study.dao.file.common import get_all_area_matrices, save_area_matrices
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

from typing_extensions import override

from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.storage.rawstudy.model.filesystem.config.hydro import (
    parse_hydro_management,
    parse_inflow_structure,
    serialize_hydro_management,
    serialize_inflow_structure,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

HYDRO_PATH = ["input", "hydro", "hydro"]
CORRELATION_PATH = ["input", "hydro", "prepro", "correlation", "annual"]


def get_inflow_path(area_id: str) -> list[str]:
    return ["input", "hydro", "prepro", area_id, "prepro", "prepro"]


def get_allocation_path(area_id: str) -> list[str]:
    return ["input", "hydro", "allocation", area_id]


def _get_max_daily_gen_energy_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"maxDailyGenEnergy_{area_id}"]


def _get_max_daily_pump_energy_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"maxDailyPumpEnergy_{area_id}"]


def _get_max_hourly_gen_power_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "series", area_id, "maxHourlyGenPower"]


def _get_max_hourly_pump_power_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "series", area_id, "maxHourlyPumpPower"]


def _get_max_power_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"maxpower_{area_id}"]


def _get_reservoir_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"reservoir_{area_id}"]


def _get_energy_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "prepro", area_id, "energy"]


def _get_run_of_river_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "series", area_id, "ror"]


def _get_modulation_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "series", area_id, "mod"]


def _get_credit_modulations_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"creditmodulations_{area_id}"]


def _get_inflow_pattern_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"inflowPattern_{area_id}"]


def _get_water_values_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "common", "capacity", f"waterValues_{area_id}"]


def _get_min_gen_path(area_id: AreaId) -> list[str]:
    return ["input", "hydro", "series", area_id, "mingen"]


class FileStudyHydroDao(HydroDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_hydro_properties(self) -> dict[str, HydroProperties]:
        """
        Return all hydro properties for all areas within a study.
        """
        all_hydro_properties = {}

        file_study = self.get_file_study()
        file_data = file_study.tree.get(HYDRO_PATH)

        for area_id in file_study.config.areas:
            hydro_management = parse_hydro_management(area_id, file_data, file_study.config.version)
            inflow_structure = self.get_inflow_structure(area_id)
            hydro_properties = HydroProperties(management_options=hydro_management, inflow_structure=inflow_structure)

            all_hydro_properties[area_id] = hydro_properties

        return all_hydro_properties

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        file_study = self.get_file_study()
        file_data = file_study.tree.get(HYDRO_PATH)
        return parse_hydro_management(area_id, file_data, file_study.config.version)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        file_study = self.get_file_study()
        file_data = file_study.tree.get(get_inflow_path(area_id))
        return parse_inflow_structure(file_data)

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        file_study = self.get_file_study()
        ini_content = file_study.tree.get(get_allocation_path(area_id))
        # allocation format can differ from the number of '[' (i.e. [[allocation]] or [allocation])
        allocation_data = ini_content.get("[allocation]", ini_content.get("allocation")) or {}
        allocations = []
        for area_name, coefficient in allocation_data.items():
            # Checks the written area exists in the study
            area_id = transform_name_to_id(area_name)
            if area_id not in file_study.config.areas:
                raise AreaNotFound(area_id)
            allocations.append(HydroAllocationArea(area_id=area_id, coefficient=coefficient))
        return HydroAllocation(allocation=allocations)

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        file_study = self.get_file_study()
        all_areas = file_study.config.areas
        return {area_id: self.get_hydro_allocation(area_id) for area_id in sorted(all_areas)}

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        return self.get_hydro_correlation_matrix().to_hydro_correlations()[area_id]

    @override
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        file_study = self.get_file_study()
        all_areas = file_study.config.areas
        area_ids = sorted(all_areas)
        array = np.identity(len(area_ids))

        try:
            ini_content = file_study.tree.get(CORRELATION_PATH)
        except (ChildNotFoundError, KeyError):
            ini_content = {}

        for key, value in ini_content.items():
            area_name1, area_name2 = key.split("%")
            area1, area2 = transform_name_to_id(area_name1), transform_name_to_id(area_name2)
            # Checks area existence
            for area_id in [area1, area2]:
                if area_id not in all_areas:
                    raise AreaNotFound(area_id)

            i = area_ids.index(area1)
            j = area_ids.index(area2)
            array[i][j] = value
            array[j][i] = value

        return HydroCorrelationMatrix(index=area_ids, columns=area_ids, data=array)

    @override
    def save_hydro_correlation(self, correlation_dict: dict[AreaId, HydroCorrelation]) -> None:
        file_study = self.get_file_study()
        all_areas = file_study.config.areas
        area_ids = sorted(all_areas)
        # Checks area existence
        for area_id, correlation in correlation_dict.items():
            if area_id not in all_areas:
                raise AreaNotFound(area_id)
            for corr in correlation.correlation:
                if corr.area_id not in all_areas:
                    raise AreaNotFound(corr.area_id)
        # Perform the save
        current_correlation_matrix = self.get_hydro_correlation_matrix()
        for area_id, correlation in correlation_dict.items():
            current_correlation_matrix.set_correlation(area_id, correlation)
        # Save data inside the file
        correlation_cfg: dict[str, float] = {}
        count = len(area_ids)
        for i in range(count):
            # not saved: values from the diagonal are always == 1.0
            for j in range(i + 1, count):
                coefficient = current_correlation_matrix.data[i][j]
                if not coefficient:
                    # null values are not saved
                    continue
                a1 = area_ids[i]
                a2 = area_ids[j]
                correlation_cfg[f"{a1}%{a2}"] = coefficient

        file_study.tree.save(correlation_cfg, CORRELATION_PATH)

    @override
    def save_hydro_management(self, hydro_management: dict[AreaId, HydroManagement]) -> None:
        file_study = self.get_file_study()
        study_version = file_study.config.version
        initial_hydro_data = file_study.tree.get(HYDRO_PATH)

        final_hydro_data = {**initial_hydro_data}  # Start with a copy of the initial data

        for area_id, management in hydro_management.items():
            new_hydro_data = serialize_hydro_management(management, area_id, study_version)
            for key, data in new_hydro_data.items():
                final_hydro_data.setdefault(key, {}).update(data)

        file_study.tree.save(final_hydro_data, HYDRO_PATH)

    @override
    def save_inflow_structure(self, inflow_structure: dict[AreaId, InflowStructure]) -> None:
        file_study = self.get_file_study()
        for area_id, inflow in inflow_structure.items():
            inflow_path = get_inflow_path(area_id)
            file_data = serialize_inflow_structure(inflow)
            file_study.tree.save(file_data, inflow_path)

    @override
    def save_hydro_allocation(self, allocation_dict: dict[AreaId, HydroAllocation]) -> None:
        file_study = self.get_file_study()
        # Checks the given areas exist in the study
        existing_areas = file_study.config.areas
        for area_id in allocation_dict:
            if area_id not in existing_areas:
                raise AreaNotFound(area_id)
        # Perform the save for each area individually
        for area_id, allocation in allocation_dict.items():
            data = {}
            for alloc in allocation.allocation:
                if alloc.area_id not in existing_areas:
                    raise AreaNotFound(alloc.area_id)
                data[alloc.area_id] = alloc.coefficient
            # Saves the data inside the file
            url = get_allocation_path(area_id)
            file_study.tree.save({"[allocation]": data}, url)

    @override
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        url = _get_max_power_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        url = _get_reservoir_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        url = _get_energy_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        url = _get_run_of_river_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        url = _get_modulation_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        url = _get_credit_modulations_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        url = _get_inflow_pattern_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        url = _get_water_values_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        url = _get_min_gen_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        url = _get_max_hourly_gen_power_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        url = _get_max_hourly_pump_power_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        url = _get_max_daily_gen_energy_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        url = _get_max_daily_pump_energy_path(area_id)
        return self.get_impl().get_matrix(url)

    @override
    def save_hydro_maxpower(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_max_power_path)

    @override
    def save_hydro_reservoir(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_reservoir_path)

    @override
    def save_hydro_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_energy_path)

    @override
    def save_hydro_run_of_river(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_run_of_river_path)

    @override
    def save_hydro_modulation(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_modulation_path)

    @override
    def save_hydro_credit_modulations(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_credit_modulations_path)

    @override
    def save_hydro_inflow_pattern(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_inflow_pattern_path)

    @override
    def save_hydro_water_values(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_water_values_path)

    @override
    def save_hydro_mingen(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_min_gen_path)

    @override
    def save_hydro_max_hourly_gen_power(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_max_hourly_gen_power_path)

    @override
    def save_hydro_max_hourly_pump_power(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_max_hourly_pump_power_path)

    @override
    def save_hydro_max_daily_gen_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_max_daily_gen_energy_path)

    @override
    def save_hydro_max_daily_pump_energy(self, series: AreaSeriesMapping) -> None:
        save_area_matrices(self.get_impl(), self.get_file_study(), series, _get_max_daily_pump_energy_path)

    def _get_all_capacity_matrices(self, prefix: str) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        matrix_nodes = {}

        folder_node = study_data.tree.get_node(["input", "hydro", "common", "capacity"])
        assert isinstance(folder_node, FolderNode)
        tree = folder_node.build()
        for node_id, node in tree.items():
            assert isinstance(node, MatrixNode)
            if node_id.startswith(prefix):
                # We only keep the matrices with the rigth prefix
                matrix_nodes[node] = node_id.removeprefix(f"{prefix}_")

        matrices_mapping = self.get_impl().get_matrices_ids(list(matrix_nodes))

        result: AreaSeriesMapping = {}
        for node, matrix_id in matrices_mapping.items():
            area_id = matrix_nodes[node]
            result[area_id] = matrix_id

        return result

    @override
    def get_all_hydro_maxpower(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("max_power")

    @override
    def get_all_hydro_reservoir(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("reservoir")

    @override
    def get_all_hydro_energy(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_energy_path)

    @override
    def get_all_hydro_run_of_river(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_run_of_river_path)

    @override
    def get_all_hydro_modulation(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_modulation_path)

    @override
    def get_all_hydro_credit_modulations(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("creditmodulations")

    @override
    def get_all_hydro_inflow_pattern(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("inflowPattern")

    @override
    def get_all_hydro_water_values(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("waterValues")

    @override
    def get_all_hydro_mingen(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_min_gen_path)

    @override
    def get_all_hydro_max_hourly_gen_power(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_max_hourly_gen_power_path)

    @override
    def get_all_hydro_max_hourly_pump_power(self) -> AreaSeriesMapping:
        study_data = self.get_file_study()
        return get_all_area_matrices(self.get_impl(), study_data, _get_max_hourly_pump_power_path)

    @override
    def get_all_hydro_max_daily_gen_energy(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("maxDailyGenEnergy")

    @override
    def get_all_hydro_max_daily_pump_energy(self) -> AreaSeriesMapping:
        return self._get_all_capacity_matrices("maxDailyPumpEnergy")

    @override
    def convert_hydro_pmax(
        self,
        hydro_pmax: HydroPmax,
    ) -> None:
        compatibility_data = self.get_impl().get_compatibility_parameters()
        # If hydro-pmax isn't changed, we don't need to do anything
        if compatibility_data.hydro_pmax == hydro_pmax:
            return

        matrix_service = self.get_impl().matrix_service
        file_study = self.get_file_study()
        areas = file_study.config.areas.keys()

        hourly_matrix_id = self.get_impl().generator_matrix_constants.get_null_matrix()
        daily_matrix_id = MATRIX_PROTOCOL_PREFIX + matrix_service.create(create_polars_dataframe(np.full((365, 1), 24)))

        if hydro_pmax == HydroPmax.HOURLY:
            max_hourly_gen_power = {}
            max_hourly_pump_power = {}
            max_daily_gen_power = {}
            max_daily_pump_power = {}
            for area_id in areas:
                max_hourly_gen_power[area_id] = hourly_matrix_id
                max_hourly_pump_power[area_id] = hourly_matrix_id
                max_daily_gen_power[area_id] = daily_matrix_id
                max_daily_pump_power[area_id] = daily_matrix_id
            self.save_hydro_max_hourly_gen_power(max_hourly_gen_power)
            self.save_hydro_max_hourly_pump_power(max_hourly_pump_power)
            self.save_hydro_max_daily_gen_energy(max_daily_gen_power)
            self.save_hydro_max_daily_pump_energy(max_daily_pump_power)

        else:
            for area_id in areas:
                file_study.tree.delete(_get_max_hourly_gen_power_path(area_id))
                file_study.tree.delete(_get_max_hourly_pump_power_path(area_id))
                file_study.tree.delete(_get_max_daily_gen_energy_path(area_id))
                file_study.tree.delete(_get_max_daily_pump_energy_path(area_id))
        # Update compatibility_data object and save it
        compatibility_data.hydro_pmax = hydro_pmax
        self.get_impl().save_compatibility_parameters(compatibility_data)
