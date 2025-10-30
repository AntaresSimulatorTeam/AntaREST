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
from typing import Sequence

from antares.study.version import StudyVersion

from antarest.core.exceptions import ChildNotFoundError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.hydro_model import HydroProperties
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
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
        self._convert_areas()
        # todo: matrices are not in the DAO ...

        # Links

        # Binding constraints

        # Xpansion

        # User resources

        # Settings

        # Scenario Builder

    def _convert_areas(self) -> None:
        area_properties = self._source_dao.get_all_area_properties()
        areas_ui = self._source_dao.get_all_areas_ui_info()
        area_names_and_thermals = {a.id: a for a in self._source_dao.get_all_areas_info()}
        st_storages = self._source_dao.get_all_st_storages()
        st_storages_constraints = self._source_dao.get_all_st_storage_additional_constraints()
        hydro_properties = self._source_dao.get_all_hydro_properties()
        try:
            renewable_clusters = self._source_dao.get_all_renewables()
        except ChildNotFoundError:  # Can happen, according to the enr-modeling
            renewable_clusters = {}

        for area_id in area_properties:
            area_name = area_names_and_thermals[area_id].name
            self._new_dao.save_area(area_name)

            # Properties
            self._new_dao.save_area_properties(area_id, area_properties[area_id])

            # Ui
            source_ui = areas_ui[area_id]
            for layer, x in source_ui.layer_x.items():
                y = source_ui.layer_y[layer]
                color = source_ui.layer_color[layer]
                color_rgb = (int(c) for c in color.strip(" ").split(","))
                area_ui = AreaUI(x=x, y=y, color_rgb=color_rgb)
                self._new_dao.save_area_ui(area_id, layer, area_ui)

            # Hydro
            self._convert_hydro(area_id, hydro_properties[area_id])

            # Thermals
            thermals = area_names_and_thermals[area_id].thermals or []
            self._convert_thermal_clusters(area_id, thermals)

            # Renewables
            if self._study_version >= STUDY_VERSION_8_1:
                renewables = list(renewable_clusters.get(area_id, {}).values())
                self._convert_renewable_clusters(area_id, renewables)

            # Short-term storages
            if self._study_version >= STUDY_VERSION_8_6:
                storages = list(st_storages[area_id].values())
                self._convert_short_term_storages(area_id, storages, st_storages_constraints.get(area_id, {}))

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

    def _convert_renewable_clusters(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        self._new_dao.save_renewables(area_id, renewables)
        for renewable in renewables:
            series_id = self._matrix_service.create(self._source_dao.get_renewable_series(area_id, renewable.id))
            self._new_dao.save_renewable_series(area_id, renewable.id, series_id)

    def _convert_short_term_storages(
        self, area_id: str, storages: list[STStorage], constraints: dict[str, list[STStorageAdditionalConstraint]]
    ) -> None:
        self._new_dao.save_st_storages(area_id, storages)
        for st_storage in storages:
            sts_id = st_storage.id
            p_max_inj_id = self._matrix_service.create(self._source_dao.get_st_storage_pmax_injection(area_id, sts_id))
            self._new_dao.save_st_storage_pmax_injection(area_id, sts_id, p_max_inj_id)

            p_max_wit_id = self._matrix_service.create(self._source_dao.get_st_storage_pmax_withdrawal(area_id, sts_id))
            self._new_dao.save_st_storage_pmax_withdrawal(area_id, sts_id, p_max_wit_id)

            low_id = self._matrix_service.create(self._source_dao.get_st_storage_lower_rule_curve(area_id, sts_id))
            self._new_dao.save_st_storage_lower_rule_curve(area_id, sts_id, low_id)

            upper_id = self._matrix_service.create(self._source_dao.get_st_storage_upper_rule_curve(area_id, sts_id))
            self._new_dao.save_st_storage_upper_rule_curve(area_id, sts_id, upper_id)

            inflows_id = self._matrix_service.create(self._source_dao.get_st_storage_inflows(area_id, sts_id))
            self._new_dao.save_st_storage_inflows(area_id, sts_id, inflows_id)

            if self._study_version >= STUDY_VERSION_9_2:
                self._new_dao.save_st_storage_additional_constraints(area_id, sts_id, constraints[sts_id])

                cost_injection = self._source_dao.get_st_storage_cost_injection(area_id, sts_id)
                injection_id = self._matrix_service.create(cost_injection)
                self._new_dao.save_st_storage_cost_injection(area_id, sts_id, injection_id)

                cost_withdrawal = self._source_dao.get_st_storage_cost_withdrawal(area_id, sts_id)
                withdrawal_id = self._matrix_service.create(cost_withdrawal)
                self._new_dao.save_st_storage_cost_withdrawal(area_id, sts_id, withdrawal_id)

                cost_level = self._source_dao.get_st_storage_cost_level(area_id, sts_id)
                cost_level_id = self._matrix_service.create(cost_level)
                self._new_dao.save_st_storage_cost_level(area_id, sts_id, cost_level_id)

                cost_var_injection = self._source_dao.get_st_storage_cost_variation_injection(area_id, sts_id)
                cost_var_injection_id = self._matrix_service.create(cost_var_injection)
                self._new_dao.save_st_storage_cost_variation_injection(area_id, sts_id, cost_var_injection_id)

                cost_var_withdrawal = self._source_dao.get_st_storage_cost_variation_withdrawal(area_id, sts_id)
                cost_var_withdrawal_id = self._matrix_service.create(cost_var_withdrawal)
                self._new_dao.save_st_storage_cost_variation_withdrawal(area_id, sts_id, cost_var_withdrawal_id)

    def _convert_hydro(self, area_id: str, properties: HydroProperties) -> None:
        self._new_dao.save_hydro_management(properties.management_options, area_id)
        self._new_dao.save_inflow_structure(properties.inflow_structure, area_id)
        self._new_dao.save_hydro_allocation(area_id, self._source_dao.get_hydro_allocation(area_id))
        self._new_dao.save_hydro_correlation(area_id, self._source_dao.get_hydro_correlation(area_id))
