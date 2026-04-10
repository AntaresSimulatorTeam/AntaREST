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

import polars as pl
from antares.study.version import StudyVersion

from antarest.core.exceptions import ChildNotFoundError, XpansionConfigurationDoesNotExist
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.binding_constraint_model import BindingConstraintOperator
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.hydro_model import HydroProperties
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao, StudyDao
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_9_2,
)


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

        # Links
        self._convert_links()

        # Binding constraints
        self._convert_binding_constraints()

        # Xpansion
        self._convert_xpansion()

        # User resources
        for user_resource in self._source_dao.get_all_user_resources():
            self._new_dao.save_user_resource(user_resource)

        # Settings
        self._convert_settings()

        # Scenario Builder
        self._new_dao.save_scenario_builder(self._source_dao.get_ruleset())

        # Districts
        for district in self._source_dao.get_districts():
            self._new_dao.save_district(district)

        # Layers
        for layer in self._source_dao.get_layers():
            self._new_dao.save_layer(layer)

    def _convert_settings(self) -> None:
        self._new_dao.save_general_config(self._source_dao.get_general_config())
        self._new_dao.save_playlist_config(self._source_dao.get_playlist_config())
        self._new_dao.save_timeseries_config(self._source_dao.get_timeseries_config())
        self._new_dao.save_advanced_parameters(self._source_dao.get_advanced_parameters())
        self._new_dao.save_optimization_preferences(self._source_dao.get_optimization_preferences())
        self._new_dao.save_thematic_trimming(self._source_dao.get_thematic_trimming())
        if self._study_version >= STUDY_VERSION_8_3:
            self._new_dao.save_adequacy_patch_parameters(self._source_dao.get_adequacy_patch_parameters())
        if self._study_version >= STUDY_VERSION_9_2:
            self._new_dao.save_compatibility_parameters(self._source_dao.get_compatibility_parameters())

    def _convert_xpansion(self) -> None:
        try:
            settings = self._source_dao.get_xpansion_settings()
        except (ChildNotFoundError, XpansionConfigurationDoesNotExist):
            # The source study does not contain an Xpansion configuration. We should return immediately
            return

        self._new_dao.create_xpansion_configuration()
        self._new_dao.save_xpansion_settings(settings)
        # Candidates
        for candidate in self._source_dao.get_all_xpansion_candidates():
            self._new_dao.save_xpansion_candidate(candidate)
        # Adequacy criterion
        self._new_dao.save_xpansion_adequacy_criterion(self._source_dao.get_xpansion_adequacy_criterion())
        # Resources
        for resource_type in XpansionResourceFileType:
            resources = self._source_dao.get_xpansion_resources(resource_type)
            for filename in resources:
                content = self._source_dao.get_xpansion_resource(resource_type, filename)

                if resource_type == XpansionResourceFileType.WEIGHTS:
                    assert isinstance(content, pl.DataFrame)
                    self._new_dao.save_xpansion_weight(filename, self._matrix_service.create(content))
                elif resource_type == XpansionResourceFileType.CAPACITIES:
                    assert isinstance(content, pl.DataFrame)
                    self._new_dao.save_xpansion_capacity(filename, self._matrix_service.create(content))
                else:
                    assert isinstance(content, bytes)
                    self._new_dao.save_xpansion_constraint(filename, content)

    def _convert_binding_constraints(self) -> None:
        constraints = list(self._source_dao.get_all_constraints().values())
        self._new_dao.save_constraints(constraints)

        for constraint in constraints:
            bc_id = constraint.id
            if self._study_version < STUDY_VERSION_8_7:
                matrix_id = self._matrix_service.create(self._source_dao.get_constraint_values_matrix(bc_id))
                self._new_dao.save_constraint_values_matrix(bc_id, matrix_id)
            else:
                if constraint.operator in {BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH}:
                    matrix_id = self._matrix_service.create(self._source_dao.get_constraint_less_term_matrix(bc_id))
                    self._new_dao.save_constraint_less_term_matrix(bc_id, matrix_id)
                if constraint.operator in {BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH}:
                    matrix_id = self._matrix_service.create(self._source_dao.get_constraint_greater_term_matrix(bc_id))
                    self._new_dao.save_constraint_greater_term_matrix(bc_id, matrix_id)
                if constraint.operator == BindingConstraintOperator.EQUAL:
                    matrix_id = self._matrix_service.create(self._source_dao.get_constraint_equal_term_matrix(bc_id))
                    self._new_dao.save_constraint_equal_term_matrix(bc_id, matrix_id)

    def _convert_links(self) -> None:
        links = self._source_dao.get_links()
        self._new_dao.save_links(links)

        # Link matrices
        self._new_dao.save_link_series(self._source_dao.get_all_links_series())
        if self._study_version >= STUDY_VERSION_8_2:
            self._new_dao.save_link_direct_capacities(self._source_dao.get_all_links_direct_capacities())
            self._new_dao.save_link_indirect_capacities(self._source_dao.get_all_links_indirect_capacities())

    def _convert_areas(self) -> None:
        area_properties = self._source_dao.get_all_area_properties()
        areas_ui = self._source_dao.get_all_areas_ui_info()
        area_names_and_thermals = {a.id: a for a in self._source_dao.get_all_areas_info()}
        hydro_properties = self._source_dao.get_all_hydro_properties()
        try:
            renewable_clusters = self._source_dao.get_all_renewables()
            st_storages = self._source_dao.get_all_st_storages()
            st_storages_constraints = self._source_dao.get_all_st_storage_additional_constraints()
        except ChildNotFoundError:  # Can happen, according to the enr-modeling and to the study version
            renewable_clusters = {}
            st_storages = {}
            st_storages_constraints = {}

        # First create all areas to avoid config issues
        for area_id in area_properties:
            area_name = area_names_and_thermals[area_id].name
            self._new_dao.save_area(area_name)

        # Thermals
        thermals = {area_info.id: area_info.thermals or [] for area_info in area_names_and_thermals.values()}
        self._convert_thermal_clusters(thermals)

        # Renewables
        if self._study_version >= STUDY_VERSION_8_1 and renewable_clusters:
            renewables = {area_id: list(value.values()) for area_id, value in renewable_clusters.items()}
            self._convert_renewable_clusters(renewables)

        # Various area matrices
        self._new_dao.save_load(self._source_dao.get_all_load())
        self._new_dao.save_solar(self._source_dao.get_all_solar())
        self._new_dao.save_wind(self._source_dao.get_all_wind())
        self._new_dao.save_reserves(self._source_dao.get_all_reserves())
        self._new_dao.save_misc_gen(self._source_dao.get_all_misc_gen())

        for area_id in area_properties:
            # Properties
            self._new_dao.save_area_properties(area_id, area_properties[area_id])

            # Ui
            source_ui = areas_ui[area_id]
            for layer, x in source_ui.layer_x.items():
                y = source_ui.layer_y[layer]
                color = source_ui.layer_color[layer]
                r, g, b = (int(c) for c in color.strip(" ").split(","))
                area_ui = AreaUI(x=x, y=y, color_rgb=(r, g, b))
                self._new_dao.save_area_ui(area_id, layer, area_ui)

            # Hydro
            self._convert_hydro(area_id, hydro_properties[area_id])

            # Short-term storages
            if self._study_version >= STUDY_VERSION_8_6:
                storages = list(st_storages.get(area_id, {}).values())
                self._convert_short_term_storages(area_id, storages, st_storages_constraints.get(area_id, {}))

    def _convert_thermal_clusters(self, data: dict[str, list[ThermalCluster]]) -> None:
        self._new_dao.save_thermals(data)

        # Matrices
        prepro_mapping = self._source_dao.get_all_thermals_prepro()
        self._new_dao.save_thermal_prepro(prepro_mapping)

        modulation_mapping = self._source_dao.get_all_thermals_modulation()
        self._new_dao.save_thermal_modulation(modulation_mapping)

        series_mapping = self._source_dao.get_all_thermals_series()
        self._new_dao.save_thermal_series(series_mapping)

        if self._study_version >= STUDY_VERSION_8_7:
            fuel_cost_mapping = self._source_dao.get_all_thermals_fuel_cost()
            self._new_dao.save_thermal_fuel_cost(fuel_cost_mapping)

            co2_cost_mapping = self._source_dao.get_all_thermals_co2_cost()
            self._new_dao.save_thermal_co2_cost(co2_cost_mapping)

    def _convert_renewable_clusters(self, data: dict[str, list[RenewableCluster]]) -> None:
        self._new_dao.save_renewables(data)

        # Matrices
        series_mapping = self._source_dao.get_all_renewables_series()
        self._new_dao.save_renewable_series(series_mapping)

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
                storage_constraints = constraints.get(sts_id)
                if storage_constraints:
                    self._new_dao.save_st_storage_additional_constraints(area_id, sts_id, storage_constraints)
                    for constraint in storage_constraints:
                        rhs_matrix = self._source_dao.get_st_storage_additional_constraint_matrix(
                            area_id, sts_id, constraint.id
                        )
                        rhs_matrix_id = self._matrix_service.create(rhs_matrix)
                        self._new_dao.save_st_storage_constraint_matrix(area_id, sts_id, constraint.id, rhs_matrix_id)

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

        # Matrices
        energy = self._matrix_service.create(self._source_dao.get_hydro_energy(area_id))
        self._new_dao.save_hydro_energy(area_id, energy)

        run_of_river = self._matrix_service.create(self._source_dao.get_hydro_run_of_river(area_id))
        self._new_dao.save_hydro_run_of_river(area_id, run_of_river)

        modulation = self._matrix_service.create(self._source_dao.get_hydro_modulation(area_id))
        self._new_dao.save_hydro_modulation(area_id, modulation)

        max_power = self._matrix_service.create(self._source_dao.get_hydro_maxpower(area_id))
        self._new_dao.save_hydro_maxpower(area_id, max_power)

        reservoir = self._matrix_service.create(self._source_dao.get_hydro_reservoir(area_id))
        self._new_dao.save_hydro_reservoir(area_id, reservoir)

        if self._study_version > STUDY_VERSION_6_5:
            credit_modulations = self._matrix_service.create(self._source_dao.get_hydro_credit_modulations(area_id))
            self._new_dao.save_hydro_credit_modulations(area_id, credit_modulations)

            inflow_pattern = self._matrix_service.create(self._source_dao.get_hydro_inflow_pattern(area_id))
            self._new_dao.save_hydro_inflow_pattern(area_id, inflow_pattern)

            water_values = self._matrix_service.create(self._source_dao.get_hydro_water_values(area_id))
            self._new_dao.save_hydro_water_values(area_id, water_values)

        if self._study_version >= STUDY_VERSION_8_6:
            mingen = self._matrix_service.create(self._source_dao.get_hydro_mingen(area_id))
            self._new_dao.save_hydro_mingen(area_id, mingen)

        if self._study_version >= STUDY_VERSION_9_2:
            compatibility_data = self._source_dao.get_compatibility_parameters()
            if compatibility_data.hydro_pmax == HydroPmax.HOURLY:
                max_hourly_gen = self._matrix_service.create(self._source_dao.get_hydro_max_hourly_gen_power(area_id))
                self._new_dao.save_hydro_max_hourly_gen_power(area_id, max_hourly_gen)

                max_hourly_pump = self._matrix_service.create(self._source_dao.get_hydro_max_hourly_pump_power(area_id))
                self._new_dao.save_hydro_max_hourly_pump_power(area_id, max_hourly_pump)

                max_daily_gen = self._matrix_service.create(self._source_dao.get_hydro_max_daily_gen_energy(area_id))
                self._new_dao.save_hydro_max_daily_gen_energy(area_id, max_daily_gen)

                max_daily_pump = self._matrix_service.create(self._source_dao.get_hydro_max_daily_pump_energy(area_id))
                self._new_dao.save_hydro_max_daily_pump_energy(area_id, max_daily_pump)
