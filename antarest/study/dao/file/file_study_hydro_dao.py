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
from typing import TYPE_CHECKING, Dict

import numpy as np
import polars as pl

from antarest.core.exceptions import AreaNotFound, ChildNotFoundError
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

from typing_extensions import override

from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService
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


class FileStudyHydroDao(HydroDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_hydro_properties(self) -> Dict[str, HydroProperties]:
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
        allocation_data = ini_content.get("[allocation]", ini_content.get("allocation", {}))
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
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        file_study = self.get_file_study()
        all_areas = file_study.config.areas
        area_ids = sorted(all_areas)
        # Checks area existence
        if area_id not in all_areas:
            raise AreaNotFound(area_id)
        for corr in correlation.correlation:
            if corr.area_id not in all_areas:
                raise AreaNotFound(corr.area_id)
        current_correlation_matrix = self.get_hydro_correlation_matrix()
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
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        file_study = self.get_file_study()
        initial_hydro_data = file_study.tree.get(HYDRO_PATH)
        new_hydro_data = serialize_hydro_management(hydro_management, area_id, file_study.config.version)
        final_hydro_data = {key: {**initial_hydro_data.get(key, {}), **value} for key, value in new_hydro_data.items()}
        file_study.tree.save(final_hydro_data, HYDRO_PATH)

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        file_study = self.get_file_study()
        inflow_path = get_inflow_path(area_id)
        file_data = serialize_inflow_structure(inflow_structure)
        file_study.tree.save(file_data, inflow_path)

    @override
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        file_study = self.get_file_study()
        # Checks the given areas exist in the study
        existing_areas = file_study.config.areas
        if area_id not in existing_areas:
            raise AreaNotFound(area_id)
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
        url = ["input", "hydro", "common", "capacity", f"maxpower_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"reservoir_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "prepro", area_id, "energy"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "series", area_id, "ror"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "series", area_id, "mod"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"creditmodulations_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"inflowPattern_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"waterValues_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "series", area_id, "mingen"]
        return self.get_impl().get_matrix(url)

    @override
    def save_hydro_maxpower(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"maxpower_{area_id}"])

    @override
    def save_hydro_reservoir(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"reservoir_{area_id}"])

    @override
    def save_hydro_energy(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "prepro", area_id, "energy"])

    @override
    def save_hydro_run_of_river(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "series", area_id, "ror"])

    @override
    def save_hydro_modulation(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "series", area_id, "mod"])

    @override
    def save_hydro_credit_modulations(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"creditmodulations_{area_id}"])

    @override
    def save_hydro_inflow_pattern(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"inflowPattern_{area_id}"])

    @override
    def save_hydro_water_values(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"waterValues_{area_id}"])

    @override
    def save_hydro_mingen(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "series", area_id, "mingen"])

    @override
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "series", area_id, "maxHourlyGenPower"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "series", area_id, "maxHourlyPumpPower"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"maxDailyGenEnergy_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        url = ["input", "hydro", "common", "capacity", f"maxDailyPumpEnergy_{area_id}"]
        return self.get_impl().get_matrix(url)

    @override
    def save_hydro_max_hourly_gen_power(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "series", area_id, "maxHourlyGenPower"])

    @override
    def save_hydro_max_hourly_pump_power(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "series", area_id, "maxHourlyPumpPower"])

    @override
    def save_hydro_max_daily_gen_energy(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"maxDailyGenEnergy_{area_id}"])

    @override
    def save_hydro_max_daily_pump_energy(self, area_id: str, series_id: str) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(series_id, ["input", "hydro", "common", "capacity", f"maxDailyPumpEnergy_{area_id}"])

    @override
    def convert_hydro_pmax(
        self,
        hydro_pmax: HydroPmax,
        matrix_service: ISimpleMatrixService,
    ) -> None:
        hourly_matrix_mapping: dict[str, dict[str, str]] = {}
        daily_matrix_mapping: dict[str, dict[str, str]] = {}

        file_study = self.get_file_study()
        areas = file_study.config.areas.keys()

        for area_id in areas:
            # when we go to hourly, we need to create matrices
            if hydro_pmax == HydroPmax.HOURLY:
                matrix_id_gen = MATRIX_PROTOCOL_PREFIX + matrix_service.create(
                    create_polars_dataframe(np.zeros((8760, 1)))
                )
                matrix_id_pump = MATRIX_PROTOCOL_PREFIX + matrix_service.create(
                    create_polars_dataframe(np.zeros((8760, 1)))
                )
                hourly_matrix_mapping[area_id] = {"gen": matrix_id_gen, "pump": matrix_id_pump}

                matrix_id_gen = MATRIX_PROTOCOL_PREFIX + matrix_service.create(
                    create_polars_dataframe(np.full((365, 1), 24))
                )
                matrix_id_pump = MATRIX_PROTOCOL_PREFIX + matrix_service.create(
                    create_polars_dataframe(np.full((365, 1), 24))
                )
                daily_matrix_mapping[area_id] = {"gen": matrix_id_gen, "pump": matrix_id_pump}
            else:
                # in other case, we will delete this files because they will be pulled from maxpower file
                try:
                    file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyGenPower"])
                    file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyPumpPower"])
                    file_study.tree.delete(["input", "hydro", "common", "capacity", f"maxDailyGenEnergy_{area_id}"])
                    file_study.tree.delete(["input", "hydro", "common", "capacity", f"maxDailyPumpEnergy_{area_id}"])
                except ChildNotFoundError:
                    pass

        if hydro_pmax == HydroPmax.HOURLY:
            for area_id, matrices in hourly_matrix_mapping.items():
                try:
                    self.save_hydro_max_hourly_gen_power(area_id, matrices["gen"])
                    self.save_hydro_max_hourly_pump_power(area_id, matrices["pump"])
                    self.save_hydro_max_daily_gen_energy(area_id, daily_matrix_mapping[area_id]["gen"])
                    self.save_hydro_max_daily_pump_energy(area_id, daily_matrix_mapping[area_id]["pump"])
                except ChildNotFoundError:
                    pass
        try:
            compatibility_data = file_study.tree.get(["settings", "generaldata", "compatibility"])
        except KeyError:
            compatibility_data = {}

        # Update hydro-pmax field
        compatibility_data["hydro-pmax"] = hydro_pmax
        file_study.tree.save(compatibility_data, ["settings", "generaldata", "compatibility"])
