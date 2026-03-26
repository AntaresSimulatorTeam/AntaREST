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

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

import numpy as np
import polars as pl
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, LinkNotFound, ReferencedObjectDeletionNotAllowed
from antarest.core.utils.polars import create_polars_dataframe
from antarest.core.utils.utils import remove_first_match
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService
from antarest.study.business.model.area_model import AreaInfo, AreaUI, AreaUIData
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.binding_constraint_model import BindingConstraint, ClusterTerm, LinkTerm
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters, HydroPmax
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.district_model import District
from antarest.study.business.model.hydro_allocation_model import HydroAllocation
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationMatrix
from antarest.study.business.model.hydro_model import (
    HydroManagement,
    HydroProperties,
    InflowStructure,
)
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Ruleset,
    ScenarioType,
)
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.common import AreaId, SeriesId, ThermalId, ThermalTimeSeries
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


@dataclass(frozen=True)
class LinkKey:
    area1_id: str
    area2_id: str


@dataclass(frozen=True)
class ClusterKey:
    area_id: str
    cluster_id: str


@dataclass(frozen=True)
class AdditionalConstraintKey:
    area_id: str
    storage_id: str
    constraint_id: str


def link_key(area1_id: str, area2_id: str) -> LinkKey:
    area1_id, area2_id = sorted((area1_id, area2_id))
    return LinkKey(area1_id, area2_id)


def cluster_key(area_id: str, cluster_id: str) -> ClusterKey:
    return ClusterKey(area_id, cluster_id)


def additional_constraint_key(area_id: str, storage_id: str, constraint_id: str) -> AdditionalConstraintKey:
    return AdditionalConstraintKey(area_id, storage_id, constraint_id)


class InMemoryStudyDao(StudyDao):
    """
    In memory implementation of study DAO, mainly for testing purposes.
    TODO, warning: no version handling, no check on areas, no checks on matrices ...
    """

    def __init__(self, version: StudyVersion, matrix_service: ISimpleMatrixService) -> None:
        self._version = version
        self._matrix_service = matrix_service
        # Links
        self._links: dict[LinkKey, Link] = {}
        self._link_capacities: dict[LinkKey, str] = {}
        self._link_direct_capacities: dict[LinkKey, str] = {}
        self._link_indirect_capacities: dict[LinkKey, str] = {}
        # Thermals
        self._thermals: dict[ClusterKey, ThermalCluster] = {}
        self._thermal_prepro: dict[ClusterKey, str] = {}
        self._thermal_modulation: dict[ClusterKey, str] = {}
        self._thermal_series: dict[ClusterKey, str] = {}
        self._thermal_fuel_cost: dict[ClusterKey, str] = {}
        self._thermal_co2_cost: dict[ClusterKey, str] = {}
        # Hydro
        self._hydro_properties: dict[str, HydroProperties] = {}
        self._hydro_allocation: dict[str, HydroAllocation] = {}
        self._hydro_correlation: dict[str, HydroCorrelation] = {}
        self._hydro_maxpower: dict[str, str] = {}
        self._hydro_reservoir: dict[str, str] = {}
        self._hydro_energy: dict[str, str] = {}
        self._hydro_run_of_river: dict[str, str] = {}
        self._hydro_modulation: dict[str, str] = {}
        self._hydro_credit_modulations: dict[str, str] = {}
        self._hydro_inflow_pattern: dict[str, str] = {}
        self._hydro_water_values: dict[str, str] = {}
        self._hydro_mingen: dict[str, str] = {}
        self._hydro_max_hourly_gen_power: dict[str, str] = {}
        self._hydro_max_hourly_pump_power: dict[str, str] = {}
        self._hydro_max_daily_gen_energy: dict[str, str] = {}
        self._hydro_max_daily_pump_energy: dict[str, str] = {}
        # Renewables
        self._renewables: dict[ClusterKey, RenewableCluster] = {}
        self._renewable_series: dict[ClusterKey, str] = {}
        # Short-term storages
        self._st_storages: dict[ClusterKey, STStorage] = {}
        self._storage_pmax_injection: dict[ClusterKey, str] = {}
        self._storage_pmax_withdrawal: dict[ClusterKey, str] = {}
        self._storage_lower_rule_curve: dict[ClusterKey, str] = {}
        self._storage_upper_rule_curve: dict[ClusterKey, str] = {}
        self._storage_inflows: dict[ClusterKey, str] = {}
        self._storage_cost_injection: dict[ClusterKey, str] = {}
        self._storage_cost_withdrawal: dict[ClusterKey, str] = {}
        self._storage_cost_level: dict[ClusterKey, str] = {}
        self._storage_cost_variation_injection: dict[ClusterKey, str] = {}
        self._storage_cost_variation_withdrawal: dict[ClusterKey, str] = {}
        # Short-term storages additional constraints
        self._st_storages_constraints: STStorageAdditionalConstraintsMap = {}
        self._st_storages_constraints_matrix: dict[AdditionalConstraintKey, str] = {}
        self._st_storages_constraints_terms: dict[str, dict[str, str]] = {}
        # Binding constraints
        self._constraints: dict[str, BindingConstraint] = {}
        self._constraints_values_matrix: dict[str, str] = {}
        self._constraints_less_term_matrix: dict[str, str] = {}
        self._constraints_greater_term_matrix: dict[str, str] = {}
        self._constraints_equal_term_matrix: dict[str, str] = {}
        # General config
        self._general_config: GeneralConfig = GeneralConfig()
        # Optimization preferences config
        self._optimization_preferences: OptimizationPreferences = OptimizationPreferences()
        # Advanced parameters config
        self._advanced_parameters: AdvancedParameters = AdvancedParameters()
        # Compatibility parameters config
        self._compatibility_parameters: CompatibilityParameters = CompatibilityParameters()
        # Xpansion
        self._xpansion_candidates: dict[str, XpansionCandidate] = {}
        self._xpansion_settings: XpansionSettings = XpansionSettings()
        self._xpansion_configuration_exists: bool = False
        self._xpansion_resources: dict[XpansionResourceFileType, dict[str, bytes]] = {}
        self._xpansion_security_criterion: XpansionAdequacyCriterion = XpansionAdequacyCriterion()
        # Thematic trimming
        self._thematic_trimming: ThematicTrimming = ThematicTrimming()
        # AdequacyPatch parameters
        self._adequacy_patch_parameters: AdequacyPatchParameters = AdequacyPatchParameters()
        # TimeSeries config
        self._timeseries_config: TimeSeriesConfiguration = TimeSeriesConfiguration()
        # Districts
        self._districts: dict[str, District] = {}
        # Layer
        self._layers: list[Layer] = []
        # Comments
        self._comments = ""
        # Area names
        self._area_names: list[str] = []
        # Playlist config
        self._playlist_config = Playlist()
        # User resources
        self._user_resources: dict[PurePosixPath, str | None] = {}
        # Area Properties
        self._area_properties: dict[str, AreaProperties] = {}
        # Area UI
        self._area_ui: dict[str, AreaUI] = {}
        # Layer-Area associations (layer_id -> set of area_ids)
        self._layer_areas: dict[str, set[str]] = {}
        # Scenario Builder
        self.ruleset: Ruleset = Ruleset()
        # Load
        self._load: dict[str, str] = {}
        # Reserves
        self._reserves: dict[str, str] = {}
        # Misc-gen
        self._misc_gen: dict[str, str] = {}
        # Solar
        self._solar: dict[str, str] = {}
        # Wind
        self._wind: dict[str, str] = {}

    @override
    def get_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()

    @override
    def get_comments(self) -> str:
        return self._comments

    @override
    def save_comments(self, comments: str) -> None:
        self._comments = comments

    @override
    def update_antares_file(self, editor: str, last_save: float) -> None:
        pass

    @override
    def get_version(self) -> StudyVersion:
        return self._version

    @override
    def get_links(self) -> Sequence[Link]:
        return list(self._links.values())

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return link_key(area1_id, area2_id) in self._links

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        try:
            return self._links[link_key(area1_id, area2_id)]
        except KeyError:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")

    @override
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        matrix_id = self._link_indirect_capacities[link_key(area_from, area_to)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        matrix_id = self._link_direct_capacities[link_key(area_from, area_to)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        matrix_id = self._link_capacities[link_key(area_from, area_to)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_link(self, link: Link) -> None:
        self._links[link_key(link.area1, link.area2)] = link

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_direct_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_indirect_capacities[link_key(area_from, area_to)] = series_id

    @override
    def delete_link(self, link: Link) -> None:
        del self._links[link_key(link.area1, link.area2)]

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        all_thermals: dict[str, dict[str, ThermalCluster]] = {}
        for key, thermal_cluster in self._thermals.items():
            all_thermals.setdefault(key.area_id, {})[key.cluster_id] = thermal_cluster
        return all_thermals

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        return [thermal for key, thermal in self._thermals.items() if key.area_id == area_id]

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        return self._thermals[cluster_key(area_id, thermal_id)]

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        return cluster_key(area_id, thermal_id) in self._thermals

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        matrix_id = self._thermal_prepro[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        matrix_id = self._thermal_modulation[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        matrix_id = self._thermal_series[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        matrix_id = self._thermal_fuel_cost[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        matrix_id = self._thermal_co2_cost[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_all_thermals_co2_cost(self) -> Iterator[ThermalTimeSeries]:
        for thermal_key, matrix_id in self._thermal_co2_cost.items():
            area_id, thermal_id = thermal_key.area_id, thermal_key.cluster_id
            yield ThermalTimeSeries(area_id=area_id, thermal_id=thermal_id, series_id=matrix_id)

    @override
    def get_all_thermals_fuel_cost(self) -> Iterator[ThermalTimeSeries]:
        for thermal_key, matrix_id in self._thermal_fuel_cost.items():
            area_id, thermal_id = thermal_key.area_id, thermal_key.cluster_id
            yield ThermalTimeSeries(area_id=area_id, thermal_id=thermal_id, series_id=matrix_id)

    @override
    def get_all_thermals_series(self) -> Iterator[ThermalTimeSeries]:
        for thermal_key, matrix_id in self._thermal_series.items():
            area_id, thermal_id = thermal_key.area_id, thermal_key.cluster_id
            yield ThermalTimeSeries(area_id=area_id, thermal_id=thermal_id, series_id=matrix_id)

    @override
    def get_all_thermals_modulation(self) -> Iterator[ThermalTimeSeries]:
        for thermal_key, matrix_id in self._thermal_modulation.items():
            area_id, thermal_id = thermal_key.area_id, thermal_key.cluster_id
            yield ThermalTimeSeries(area_id=area_id, thermal_id=thermal_id, series_id=matrix_id)

    @override
    def get_all_thermals_prepro(self) -> Iterator[ThermalTimeSeries]:
        for thermal_key, matrix_id in self._thermal_prepro.items():
            area_id, thermal_id = thermal_key.area_id, thermal_key.cluster_id
            yield ThermalTimeSeries(area_id=area_id, thermal_id=thermal_id, series_id=matrix_id)

    @override
    def save_thermals(self, data: dict[AreaId, list[ThermalCluster]]) -> None:
        for area_id, thermals in data.items():
            for thermal in thermals:
                self._thermals[cluster_key(area_id, thermal.id)] = thermal

    @override
    def save_thermal_prepro(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                self._thermal_prepro[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_modulation(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                self._thermal_modulation[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_series(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                self._thermal_series[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_fuel_cost(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                self._thermal_fuel_cost[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_co2_cost(self, series: dict[AreaId, dict[ThermalId, SeriesId]]) -> None:
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                self._thermal_co2_cost[cluster_key(area_id, thermal_id)] = series_id

    @override
    def delete_thermal(self, area_id: str, thermal_id: str) -> None:
        del self._thermals[cluster_key(area_id, thermal_id)]

    @override
    def get_all_hydro_properties(self) -> dict[str, HydroProperties]:
        return self._hydro_properties

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        return self._hydro_properties[area_id].management_options

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        return self._hydro_properties[area_id].inflow_structure

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        return self._hydro_allocation[area_id]

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        return self._hydro_allocation

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        return self._hydro_correlation[area_id]

    @override
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        return HydroCorrelationMatrix.from_hydro_correlations(self._hydro_correlation)

    @override
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_max_hourly_gen_power[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_max_hourly_pump_power[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_max_daily_gen_energy[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_max_daily_pump_energy[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        self._hydro_properties[area_id].management_options = hydro_management

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        self._hydro_properties[area_id].inflow_structure = inflow_structure

    @override
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        self._hydro_allocation[area_id] = allocation

    @override
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        self._hydro_correlation[area_id] = correlation

    @override
    def save_hydro_max_hourly_gen_power(self, area_id: str, series_id: str) -> None:
        self._hydro_max_hourly_gen_power[area_id] = series_id

    @override
    def save_hydro_max_hourly_pump_power(self, area_id: str, series_id: str) -> None:
        self._hydro_max_hourly_pump_power[area_id] = series_id

    @override
    def save_hydro_max_daily_gen_energy(self, area_id: str, series_id: str) -> None:
        self._hydro_max_daily_gen_energy[area_id] = series_id

    @override
    def save_hydro_max_daily_pump_energy(self, area_id: str, series_id: str) -> None:
        self._hydro_max_daily_pump_energy[area_id] = series_id

    @override
    def convert_hydro_pmax(
        self,
        hydro_pmax: HydroPmax,
    ) -> None:
        compatibility_data = self.get_compatibility_parameters()
        # If hydro-pmax isn't changed, we don't need to do anything
        if compatibility_data.hydro_pmax == hydro_pmax:
            return

        areas = self._area_names
        matrix_service = self._matrix_service

        hourly = create_polars_dataframe(np.zeros((8760, 1)))
        daily = create_polars_dataframe(np.full((365, 1), 24))

        if hydro_pmax == HydroPmax.HOURLY:
            # When converting to hourly, create and save the matrices
            for area_id in areas:
                self.save_hydro_max_hourly_gen_power(area_id, MATRIX_PROTOCOL_PREFIX + matrix_service.create(hourly))
                self.save_hydro_max_hourly_pump_power(area_id, MATRIX_PROTOCOL_PREFIX + matrix_service.create(hourly))
                self.save_hydro_max_daily_gen_energy(area_id, MATRIX_PROTOCOL_PREFIX + matrix_service.create(daily))
                self.save_hydro_max_daily_pump_energy(area_id, MATRIX_PROTOCOL_PREFIX + matrix_service.create(daily))
        else:
            # When converting away from hourly, remove the matrices from in-memory storage
            for area_id in areas:
                self._hydro_max_hourly_gen_power.pop(area_id, None)
                self._hydro_max_hourly_pump_power.pop(area_id, None)
                self._hydro_max_daily_gen_energy.pop(area_id, None)
                self._hydro_max_daily_pump_energy.pop(area_id, None)
        # Update compatibility_data object and save it
        compatibility_data.hydro_pmax = hydro_pmax
        self.save_compatibility_parameters(compatibility_data)

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        all_renewables: dict[str, dict[str, RenewableCluster]] = {}
        for key, renewable_cluster in self._renewables.items():
            all_renewables.setdefault(key.area_id, {})[key.cluster_id] = renewable_cluster
        return all_renewables

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        return [renewable for key, renewable in self._renewables.items() if key.area_id == area_id]

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        return self._renewables[cluster_key(area_id, renewable_id)]

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        return cluster_key(area_id, renewable_id) in self._renewables

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pl.DataFrame:
        matrix_id = self._renewable_series[cluster_key(area_id, renewable_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        self._renewables[cluster_key(area_id, renewable.id)] = renewable

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        for renewable in renewables:
            self.save_renewable(area_id, renewable)

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        self._renewable_series[cluster_key(area_id, renewable_id)] = series_id

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        del self._renewables[cluster_key(area_id, renewable.id)]

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        return self._constraints

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        return self._constraints[constraint_id]

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pl.DataFrame:
        matrix_id = self._constraints_values_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        matrix_id = self._constraints_less_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        matrix_id = self._constraints_greater_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        matrix_id = self._constraints_equal_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        for constraint in constraints:
            self._constraints[constraint.id] = constraint

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_values_matrix[constraint_id] = series_id

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_less_term_matrix[constraint_id] = series_id

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_greater_term_matrix[constraint_id] = series_id

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_equal_term_matrix[constraint_id] = series_id

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        for constraint in constraints:
            del self._constraints[constraint.id]

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        all_storages: dict[str, dict[str, STStorage]] = {}
        for key, storage in self._st_storages.items():
            all_storages.setdefault(key.area_id, {})[key.cluster_id] = storage
        return all_storages

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        return [storage for key, storage in self._st_storages.items() if key.area_id == area_id]

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        return self._st_storages[cluster_key(area_id, storage_id)]

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        return cluster_key(area_id, storage_id) in self._st_storages

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_pmax_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_pmax_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_lower_rule_curve[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_upper_rule_curve[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_inflows[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_cost_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_cost_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_cost_level[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_cost_variation_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        matrix_id = self._storage_cost_variation_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_additional_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str
    ) -> pl.DataFrame:
        matrix_id = self._st_storages_constraints_matrix[additional_constraint_key(area_id, storage_id, constraint_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        self._st_storages[cluster_key(area_id, st_storage.id)] = st_storage

    @override
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        for storage in storages:
            self.save_st_storage(area_id, storage)

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_pmax_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_pmax_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_lower_rule_curve[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_upper_rule_curve[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_inflows[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_level[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_variation_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_variation_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def delete_st_storage(self, area_id: str, storage: STStorage) -> None:
        del self._st_storages[cluster_key(area_id, storage.id)]

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        self._general_config = config

    @override
    def get_general_config(self) -> GeneralConfig:
        return self._general_config

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        return self._optimization_preferences

    @override
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        self._optimization_preferences = config

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        return self._advanced_parameters

    @override
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        return self._compatibility_parameters

    @override
    def save_compatibility_parameters(self, parameters: CompatibilityParameters) -> None:
        self._compatibility_parameters = parameters

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        self._advanced_parameters = parameters

    @override
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        return self._st_storages_constraints

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        return self._st_storages_constraints.get(area_id, {}).get(storage_id, [])

    @override
    def save_st_storage_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str, series_id: str
    ) -> None:
        self._st_storages_constraints_matrix[additional_constraint_key(area_id, storage_id, constraint_id)] = series_id

    @override
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        existing_constraints = self._st_storages_constraints[area_id][storage_id]
        constraints_to_remove = []
        for constraint in existing_constraints:
            if constraint.id in constraints:
                constraints_to_remove.append(constraint)
        for constraint in constraints_to_remove:
            self._st_storages_constraints[area_id][storage_id].remove(constraint)
            self._st_storages_constraints_matrix.pop(
                additional_constraint_key(area_id, storage_id, constraint.id), None
            )

    @override
    def save_st_storage_additional_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        existing_constraints = self._st_storages_constraints.get(area_id, {}).get(storage_id, [])

        existing_map = {}
        for constraint in existing_constraints:
            existing_map[constraint.id] = constraint

        for constraint in constraints:
            existing_map[constraint.id] = constraint

        self._st_storages_constraints.setdefault(area_id, {})[storage_id] = list(existing_map.values())

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        return list(self._xpansion_candidates.values())

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        return self._xpansion_candidates[candidate_id]

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: str | None = None) -> None:
        if old_id:
            del self._xpansion_candidates[old_id]
        self._xpansion_candidates[candidate.name] = candidate

    @override
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        del self._xpansion_candidates[candidate_name]

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        return

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        return

    @override
    def get_xpansion_settings(self) -> XpansionSettings:
        return self._xpansion_settings

    @override
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        self._xpansion_settings = settings

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        return

    @override
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        return self._xpansion_resources[resource_type][filename]

    @override
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        return list(self._xpansion_resources.get(resource_type, {}).keys())

    @override
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        return

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        return self._xpansion_security_criterion

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        return self._thematic_trimming

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        self._thematic_trimming = trimming

    @override
    def get_adequacy_patch_parameters(self) -> AdequacyPatchParameters:
        return self._adequacy_patch_parameters

    @override
    def save_adequacy_patch_parameters(self, parameters: AdequacyPatchParameters) -> None:
        self._adequacy_patch_parameters = parameters

    @override
    def get_timeseries_config(self) -> TimeSeriesConfiguration:
        return self._timeseries_config

    @override
    def save_timeseries_config(self, config: TimeSeriesConfiguration) -> None:
        self._timeseries_config = config

    @override
    def create_xpansion_configuration(self) -> None:
        self._xpansion_configuration_exists = True

    @override
    def delete_xpansion_configuration(self) -> None:
        self._xpansion_configuration_exists = False

    @override
    def delete_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        del self._xpansion_resources[resource_type][filename]

    @override
    def save_xpansion_constraint(self, filename: str, content: bytes) -> None:
        self._xpansion_resources[XpansionResourceFileType.CONSTRAINTS][filename] = content

    @override
    def save_xpansion_capacity(self, filename: str, series_id: str) -> None:
        content = series_id.encode("utf-8")
        self._xpansion_resources[XpansionResourceFileType.CAPACITIES][filename] = content

    @override
    def save_xpansion_weight(self, filename: str, series_id: str) -> None:
        content = series_id.encode("utf-8")
        self._xpansion_resources[XpansionResourceFileType.WEIGHTS][filename] = content

    @override
    def get_districts(self) -> Sequence[District]:
        return list(self._districts.values())

    @override
    def get_district(self, district_id: str) -> District:
        return self._districts[district_id]

    @override
    def district_exists(self, district_id: str) -> bool:
        return district_id in self._districts

    @override
    def save_district(self, district: District) -> None:
        self._districts[district.id] = district

    @override
    def remove_district(self, district_id: str) -> None:
        del self._districts[district_id]

    @override
    def get_invalid_area_ids(self, areas: list[str]) -> list[str]:
        # TODO make this actually work once we implement area DAO
        return list(set(areas) - set(self._area_names))

    @override
    def get_all_area_ids(self) -> list[str]:
        return self._area_names

    @override
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        self._xpansion_security_criterion = criterion

    @override
    def save_layer(self, layer: Layer) -> None:
        new_id = max((int(layer.id) for layer in self._layers if layer.id is not None), default=0) + 1
        layer.id = str(new_id)
        self._layers.insert(new_id, layer)

    @override
    def get_layers(self) -> Sequence[Layer]:
        return self._layers

    @override
    def delete_layer(self, layer_id: str) -> None:
        remove_first_match(self._layers, lambda layer: layer.id == layer_id)

    @override
    def layer_exists(self, layer_id: str) -> bool:
        return any(layer.id == layer_id for layer in self._layers)

    @override
    def get_playlist_config(self) -> Playlist:
        return self._playlist_config

    @override
    def save_playlist_config(self, playlist: Playlist) -> None:
        self._playlist_config = playlist

    @override
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        for path, content in self._user_resources.items():
            resource_type = ResourceType.FOLDER if content is None else ResourceType.FILE
            yield UserResourceDataCreation(
                path=path,
                resource_type=resource_type,
                blob_id=content,
            )

    @override
    def save_user_resource(self, resource_data: UserResourceDataCreation) -> None:
        self._user_resources[resource_data.path] = resource_data.blob_id

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        del self._user_resources[resource_path]

    @override
    def get_area_properties(self, area_id: str) -> AreaProperties:
        return self._area_properties[area_id]

    @override
    def get_all_area_properties(self) -> dict[str, AreaProperties]:
        return self._area_properties

    @override
    def save_area_properties(self, area_id: str, area_properties: AreaProperties) -> None:
        self._area_properties[area_id] = area_properties

    @override
    def get_ruleset(self) -> Ruleset:
        return self.ruleset

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        return self.ruleset.get(scenario_type)

    @override
    def save_scenario_builder(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    @override
    def get_all_areas_info(self) -> list[AreaInfo]:
        return [AreaInfo(id=area_id, name=area_id, thermals=[]) for area_id in self._area_names]

    @override
    def get_all_areas_ui_info(self) -> dict[str, AreaUIData]:
        result: dict[str, AreaUIData] = {}
        for area_id, area_ui in self._area_ui.items():
            r, g, b = area_ui.color_rgb
            result[area_id] = AreaUIData(
                ui={
                    "x": area_ui.x,
                    "y": area_ui.y,
                    "color_r": r,
                    "color_g": g,
                    "color_b": b,
                    "layers": "0",
                },
                layerX={"0": area_ui.x},
                layerY={"0": area_ui.y},
                layerColor={"0": f"{r}, {g}, {b}"},
            )
        return result

    @override
    def get_area_ui(self, area_id: str, layer: str = "0") -> AreaUI:
        if area_id not in self._area_names:
            raise AreaNotFound(area_id)

        return self._area_ui.get(area_id, AreaUI())

    @override
    def save_area(self, area_name: str) -> None:
        area_id = transform_name_to_id(area_name)
        if area_id in self._area_names:
            raise ValueError(f"Area '{area_name}' already exists and could not be created")
        self._area_names.append(area_id)

        # Initialize default UI for the new area
        self._area_ui[area_id] = AreaUI()

    @override
    def delete_area(self, area_id: str) -> None:
        if area_id not in self._area_names:
            raise AreaNotFound(area_id)

        # Check that the area is not referenced in any binding constraint
        referencing_binding_constraints = []
        for bc in self._constraints.values():
            for term in bc.terms:
                data = term.data
                if (isinstance(data, ClusterTerm) and data.area == area_id) or (
                    isinstance(data, LinkTerm) and (data.area1 == area_id or data.area2 == area_id)
                ):
                    referencing_binding_constraints.append(bc)
                    break
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(area_id, binding_ids, object_type="Area")

        self._area_names.remove(area_id)

        # Clean up UI info
        self._area_ui.pop(area_id, None)

    @override
    def save_area_ui(self, area_id: str, layer: str, area_ui: AreaUI) -> None:
        if area_id not in self._area_names:
            raise AreaNotFound(area_id)

        self._area_ui[area_id] = area_ui

    @override
    def save_layer_areas(self, layer_id: str, area_ids: list[str]) -> None:
        # Verify that all areas exist
        for area_id in area_ids:
            if area_id not in self._area_names:
                raise AreaNotFound(area_id)

        self._layer_areas[layer_id] = set(area_ids)

    @override
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_maxpower[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_reservoir[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_energy[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_run_of_river[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_modulation[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_credit_modulations[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_inflow_pattern[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_water_values[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._hydro_mingen[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def save_hydro_maxpower(self, area_id: str, series_id: str) -> None:
        self._hydro_maxpower[area_id] = series_id

    @override
    def save_hydro_reservoir(self, area_id: str, series_id: str) -> None:
        self._hydro_reservoir[area_id] = series_id

    @override
    def save_hydro_energy(self, area_id: str, series_id: str) -> None:
        self._hydro_energy[area_id] = series_id

    @override
    def save_hydro_run_of_river(self, area_id: str, series_id: str) -> None:
        self._hydro_run_of_river[area_id] = series_id

    @override
    def save_hydro_modulation(self, area_id: str, series_id: str) -> None:
        self._hydro_modulation[area_id] = series_id

    @override
    def save_hydro_credit_modulations(self, area_id: str, series_id: str) -> None:
        self._hydro_credit_modulations[area_id] = series_id

    @override
    def save_hydro_inflow_pattern(self, area_id: str, series_id: str) -> None:
        self._hydro_inflow_pattern[area_id] = series_id

    @override
    def save_hydro_water_values(self, area_id: str, series_id: str) -> None:
        self._hydro_water_values[area_id] = series_id

    @override
    def save_hydro_mingen(self, area_id: str, series_id: str) -> None:
        self._hydro_mingen[area_id] = series_id

    @override
    def get_load(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._load[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_misc_gen(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._misc_gen[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_reserves(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._reserves[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_solar(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._solar[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_wind(self, area_id: str) -> pl.DataFrame:
        matrix_id = self._wind[area_id]
        return self._matrix_service.get(matrix_id)

    @override
    def save_load(self, area_id: str, series_id: str) -> None:
        self._load[area_id] = series_id

    @override
    def save_misc_gen(self, area_id: str, series_id: str) -> None:
        self._misc_gen[area_id] = series_id

    @override
    def save_reserves(self, area_id: str, series_id: str) -> None:
        self._reserves[area_id] = series_id

    @override
    def save_solar(self, area_id: str, series_id: str) -> None:
        self._solar[area_id] = series_id

    @override
    def save_wind(self, area_id: str, series_id: str) -> None:
        self._wind[area_id] = series_id
