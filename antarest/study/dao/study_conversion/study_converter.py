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

from antares.study.version import StudyVersion

from antarest.core.exceptions import ChildNotFoundError, XpansionConfigurationDoesNotExist
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao, StudyDao
from antarest.study.dao.common import AreaUiMapping
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_9_2,
    STUDY_VERSION_10_0,
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
        self._new_dao.save_user_resources(self._source_dao.get_all_user_resources())

        # Settings
        self._convert_settings()

        # Scenario Builder
        self._new_dao.save_scenario_builder(self._source_dao.get_ruleset())

        # Districts
        for district in self._source_dao.get_districts():
            self._new_dao.save_district(district)

        # Comments
        self._new_dao.save_comments(self._source_dao.get_comments())

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
        self._new_dao.save_xpansion_candidates(self._source_dao.get_all_xpansion_candidates())
        # Adequacy criterion
        self._new_dao.save_xpansion_adequacy_criterion(self._source_dao.get_xpansion_adequacy_criterion())

        # Weights
        weights = self._source_dao.get_all_xpansion_weights()
        if weights:
            self._new_dao.save_xpansion_weight(weights)

        # Capacities
        capacities = self._source_dao.get_all_xpansion_capacities()
        if capacities:
            self._new_dao.save_xpansion_capacity(capacities)

        # Constraints
        constraints = self._source_dao.get_all_xpansion_constraints()
        if constraints:
            self._new_dao.save_xpansion_constraint(constraints)

    def _convert_binding_constraints(self) -> None:
        constraints = list(self._source_dao.get_all_constraints().values())

        # If no binding constraint exists, we return immediately
        if not constraints:
            return

        self._new_dao.save_constraints(constraints)

        if self._study_version < STUDY_VERSION_8_7:
            values = self._source_dao.get_all_constraint_values_matrix()
            self._new_dao.save_constraint_values_matrix(values)

        else:
            self._new_dao.save_constraint_less_term_matrix(self._source_dao.get_all_constraint_less_term_matrix())
            self._new_dao.save_constraint_greater_term_matrix(self._source_dao.get_all_constraint_greater_term_matrix())
            self._new_dao.save_constraint_equal_term_matrix(self._source_dao.get_all_constraint_equal_term_matrix())

    def _convert_links(self) -> None:
        links = self._source_dao.get_links()

        # If no link exists, we return immediately
        if not links:
            return

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
        try:
            renewable_clusters = self._source_dao.get_all_renewables()
        except ChildNotFoundError:  # Can happen, according to the enr-modeling and to the study version
            renewable_clusters = {}

        # If no area exists, we return immediately
        if not area_properties:
            return

        # First, create all areas with their properties to avoid foreign key or config issues
        new_area_properties = {}
        for area_id in area_properties:
            new_area_properties[area_names_and_thermals[area_id].name] = area_properties[area_id]
        self._new_dao.save_areas_with_properties(new_area_properties)

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
        self._new_dao.save_misc_gen(self._source_dao.get_all_misc_gen())

        # Reserves
        if self._study_version >= STUDY_VERSION_10_0:
            self._convert_reserves()
        else:
            # Legacy reserves behavior
            self._new_dao.save_reserves(self._source_dao.get_all_reserves())

        # Hydro
        self._convert_hydro()

        # Layers (before Ui to avoid foreign key issues)
        for layer in self._source_dao.get_layers():
            self._new_dao.save_layer(layer)

        # Ui
        new_ui: AreaUiMapping = {}
        for area_id, source_ui in areas_ui.items():
            new_ui[area_id] = {}
            for layer_id, x in source_ui.layer_x.items():
                y = source_ui.layer_y[layer_id]
                color = source_ui.layer_color[layer_id]
                r, g, b = (int(c) for c in color.strip(" ").split(","))
                area_ui = AreaUI(x=x, y=y, color_rgb=(r, g, b))
                new_ui[area_id][layer_id] = area_ui
        self._new_dao.save_area_ui(new_ui)

        # Short-term storages
        if self._study_version >= STUDY_VERSION_8_6:
            st_storages = self._source_dao.get_all_st_storages()
            if st_storages:
                st_storages_constraints = {}
                if self._study_version >= STUDY_VERSION_9_2:
                    st_storages_constraints = self._source_dao.get_all_st_storage_additional_constraints()
                self._convert_short_term_storages(st_storages, st_storages_constraints)

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

    def _convert_reserves(self) -> None:
        # Global parameters
        self._new_dao.save_reserves_global_parameters(self._source_dao.get_all_reserves_global_parameters())

        # Reserve definitions
        reserve_definitions = self._source_dao.get_all_reserve_definitions()
        if reserve_definitions:
            self._new_dao.save_reserve_definitions(
                {area_id: list(reserves.values()) for area_id, reserves in reserve_definitions.items()}
            )
            self._new_dao.save_reserve_needs(self._source_dao.get_all_reserve_needs())

        # Thermal certifications
        thermal_certifications = self._source_dao.get_all_thermal_reserve_certifications()
        if thermal_certifications:
            self._new_dao.save_thermal_reserve_certifications(thermal_certifications)

        # Thermal symmetries
        thermal_symmetries = self._source_dao.get_all_thermal_reserve_symmetries()
        if thermal_symmetries:
            self._new_dao.save_thermal_reserve_symmetries(thermal_symmetries)

    def _convert_short_term_storages(
        self, storages: dict[str, dict[str, STStorage]], constraints: STStorageAdditionalConstraintsMap
    ) -> None:
        # Short-term storages
        self._new_dao.save_st_storages({area_id: list(value.values()) for area_id, value in storages.items()})

        # Matrices
        pmax_injection = self._source_dao.get_all_st_storage_pmax_injection()
        self._new_dao.save_st_storage_pmax_injection(pmax_injection)

        pmax_withdrawal = self._source_dao.get_all_st_storage_pmax_withdrawal()
        self._new_dao.save_st_storage_pmax_withdrawal(pmax_withdrawal)

        lower_rule_curve = self._source_dao.get_all_st_storage_lower_rule_curve()
        self._new_dao.save_st_storage_lower_rule_curve(lower_rule_curve)

        upper_rule_curve = self._source_dao.get_all_st_storage_upper_rule_curve()
        self._new_dao.save_st_storage_upper_rule_curve(upper_rule_curve)

        inflows = self._source_dao.get_all_st_storage_inflows()
        self._new_dao.save_st_storage_inflows(inflows)

        if self._study_version >= STUDY_VERSION_9_2:
            cost_injection = self._source_dao.get_all_st_storage_cost_injection()
            self._new_dao.save_st_storage_cost_injection(cost_injection)

            cost_withdrawal = self._source_dao.get_all_st_storage_cost_withdrawal()
            self._new_dao.save_st_storage_cost_withdrawal(cost_withdrawal)

            cost_level = self._source_dao.get_all_st_storage_cost_level()
            self._new_dao.save_st_storage_cost_level(cost_level)

            cost_var_injection = self._source_dao.get_all_st_storage_cost_variation_injection()
            self._new_dao.save_st_storage_cost_variation_injection(cost_var_injection)

            cost_var_withdrawal = self._source_dao.get_all_st_storage_cost_variation_withdrawal()
            self._new_dao.save_st_storage_cost_variation_withdrawal(cost_var_withdrawal)

        # Short-term storage constraints
        if constraints:
            self._new_dao.save_st_storage_additional_constraints(constraints)

            constraint_matrices = self._source_dao.get_all_st_storage_additional_constraint_matrices()
            self._new_dao.save_st_storage_constraint_matrices(constraint_matrices)

    def _convert_hydro(self) -> None:
        hydro_properties = self._source_dao.get_all_hydro_properties()

        # Properties
        management = {}
        inflow_structure = {}
        for area_id, properties in hydro_properties.items():
            management[area_id] = properties.management_options
            inflow_structure[area_id] = properties.inflow_structure

        self._new_dao.save_hydro_management(management)
        self._new_dao.save_inflow_structure(inflow_structure)

        # Allocation
        allocation = self._source_dao.get_hydro_allocation_matrix()
        self._new_dao.save_hydro_allocation(allocation)

        # Correlation
        correlation_dict = self._source_dao.get_hydro_correlation_matrix().to_hydro_correlations()
        self._new_dao.save_hydro_correlation(correlation_dict)

        # Matrices
        energy = self._source_dao.get_all_hydro_energy()
        self._new_dao.save_hydro_energy(energy)

        run_of_river = self._source_dao.get_all_hydro_run_of_river()
        self._new_dao.save_hydro_run_of_river(run_of_river)

        modulation = self._source_dao.get_all_hydro_modulation()
        self._new_dao.save_hydro_modulation(modulation)

        max_power = self._source_dao.get_all_hydro_maxpower()
        self._new_dao.save_hydro_maxpower(max_power)

        reservoir = self._source_dao.get_all_hydro_reservoir()
        self._new_dao.save_hydro_reservoir(reservoir)

        if self._study_version > STUDY_VERSION_6_5:
            credit_modulations = self._source_dao.get_all_hydro_credit_modulations()
            self._new_dao.save_hydro_credit_modulations(credit_modulations)

            inflow_pattern = self._source_dao.get_all_hydro_inflow_pattern()
            self._new_dao.save_hydro_inflow_pattern(inflow_pattern)

            water_values = self._source_dao.get_all_hydro_water_values()
            self._new_dao.save_hydro_water_values(water_values)

        if self._study_version >= STUDY_VERSION_8_6:
            mingen = self._source_dao.get_all_hydro_mingen()
            self._new_dao.save_hydro_mingen(mingen)

        if self._study_version >= STUDY_VERSION_9_2:
            compatibility_data = self._source_dao.get_compatibility_parameters()
            if compatibility_data.hydro_pmax == HydroPmax.HOURLY:
                max_hourly_gen = self._source_dao.get_all_hydro_max_hourly_gen_power()
                self._new_dao.save_hydro_max_hourly_gen_power(max_hourly_gen)

                max_hourly_pump = self._source_dao.get_all_hydro_max_hourly_pump_power()
                self._new_dao.save_hydro_max_hourly_pump_power(max_hourly_pump)

                max_daily_gen = self._source_dao.get_all_hydro_max_daily_gen_energy()
                self._new_dao.save_hydro_max_daily_gen_energy(max_daily_gen)

                max_daily_pump = self._source_dao.get_all_hydro_max_daily_pump_energy()
                self._new_dao.save_hydro_max_daily_pump_energy(max_daily_pump)
