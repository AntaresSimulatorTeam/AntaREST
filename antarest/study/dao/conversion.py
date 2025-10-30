# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from antares.study.version import StudyVersion

from antarest.core.exceptions import ChildNotFoundError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao, StudyDao
from antarest.study.model import STUDY_VERSION_8_1, STUDY_VERSION_8_6, STUDY_VERSION_8_7, STUDY_VERSION_9_2


class StudyConverter:
    def __init__(
        self,
        source_dao: ReadOnlyStudyDao,
        new_dao: StudyDao,
        study_version: StudyVersion,
        matrix_service: ISimpleMatrixService,
    ):
        self._source_dao = source_dao
        self._new_dao = new_dao
        self._study_version = study_version
        self._matrix_service = matrix_service

    def convert_study_inputs(self) -> None:
        # Areas
        area_properties = self._source_dao.get_all_area_properties()
        area_names_and_thermals = {a.id: a for a in self._source_dao.get_all_areas_info()}
        st_storages = self._source_dao.get_all_st_storages()
        st_storages_constraints = self._source_dao.get_all_st_storage_additional_constraints()
        hydro_properties = self._source_dao.get_all_hydro_properties()
        try:
            renewable_clusters = self._source_dao.get_all_renewables()
        except ChildNotFoundError:  # Can happen, according to the enr-modeling
            renewable_clusters = {}

        for area_id in area_properties:
            # todo: ui
            area_name = area_names_and_thermals[area_id].name
            self._new_dao.save_area(area_name)
            # Hydro

            self._new_dao.save_hydro_management(hydro_properties[area_id].management_options, area_id)
            self._new_dao.save_inflow_structure(hydro_properties[area_id].inflow_structure, area_id)
            self._new_dao.save_hydro_allocation(area_id, self._source_dao.get_hydro_allocation(area_id))
            self._new_dao.save_hydro_correlation(area_id, self._source_dao.get_hydro_correlation(area_id))
            # todo: matrices

            # Thermals
            thermals = area_names_and_thermals[area_id].thermals or []
            self._convert_thermal_clusters(area_id, thermals)

            # todo: matrices
            # Renewables
            if self._study_version >= STUDY_VERSION_8_1:
                self._new_dao.save_renewables(area_id, list(renewable_clusters.get(area_id, {}).values()))
                # todo: matrices
            # Short-term storages
            if self._study_version >= STUDY_VERSION_8_6:
                storages = list(st_storages[area_id].values())
                self._new_dao.save_st_storages(area_id, storages)
                # todo: matrices
                if self._study_version >= STUDY_VERSION_9_2:
                    for storage in storages:
                        self._new_dao.save_st_storage_additional_constraints(
                            area_id, storage.id, st_storages_constraints[area_id][storage.id]
                        )
                        # todo: matrices

    def _convert_thermal_clusters(self, area_id: str, thermals: list[ThermalCluster]) -> None:
        self._new_dao.save_thermals(area_id, thermals)
        for thermal in thermals:
            thermal_id = thermal.id
            prepro_id = self._matrix_service.create(self._source_dao.get_thermal_prepro(area_id, thermal_id))
            self._new_dao.save_thermal_prepro(area_id, thermal_id, prepro_id)

            modulation_id = self._matrix_service.create(self._source_dao.get_thermal_modulation(area_id, thermal_id))
            self._new_dao.save_thermal_modulation(area_id, thermal_id, modulation_id)

            series_id = self._matrix_service.create(self._source_dao.get_thermal_series(area_id, thermal_id))
            self._new_dao.save_thermal_series(area_id, thermal_id, series_id)

            if self._study_version >= STUDY_VERSION_8_7:
                fuel_cost_id = self._matrix_service.create(self._source_dao.get_thermal_fuel_cost(area_id, thermal_id))
                self._new_dao.save_thermal_fuel_cost(area_id, thermal_id, fuel_cost_id)

                co2_cost_id = self._matrix_service.create(self._source_dao.get_thermal_co2_cost(area_id, thermal_id))
                self._new_dao.save_thermal_co2_cost(area_id, thermal_id, co2_cost_id)
