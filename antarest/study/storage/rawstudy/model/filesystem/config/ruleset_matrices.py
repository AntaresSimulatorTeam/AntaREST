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
import dataclasses
from typing import Any, Dict, Iterable, Literal, Mapping, Optional, Tuple, TypeAlias, cast

import numpy as np
import pandas as pd

from antarest.study.business.scenario_builder_management import ScenarioType
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

SCENARIO_TYPES = {
    "l": "load",
    "h": "hydro",
    "w": "wind",
    "s": "solar",
    "t": "thermal",
    "r": "renewable",
    "ntc": "link",
    "bc": "binding-constraints",
    "hl": "hydro-initial-levels",
    "hfl": "hydro-final-levels",
    "hgp": "hydro-generation-power",
    "sts": "short-term-storage-inflows",
}

_Value: TypeAlias = int | float

RandType: TypeAlias = Literal[""]
RANDOM: RandType = ""
McScenarioMapping: TypeAlias = dict[str, _Value | RandType]


_SimpleScenario: TypeAlias = dict[str, McScenarioMapping]
_ClusterScenario: TypeAlias = dict[str, _SimpleScenario]
_Scenario: TypeAlias = _SimpleScenario | _ClusterScenario
_ScenarioMapping: TypeAlias = dict[str, _Scenario]

SimpleTableForm: TypeAlias = Dict[str, Dict[str, _Value | RandType]]
ClusterTableForm: TypeAlias = Dict[str, SimpleTableForm]
TableForm: TypeAlias = SimpleTableForm | ClusterTableForm

_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "hgp"
_BINDING_CONSTRAINTS_RELATED_SYMBOLS = ("bc",)
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r", "sts"


# ========================================
#  Formating functions for matrix indexes
# ========================================


def idx_area(area: str, /) -> str:
    return area


def idx_link(area1: str, area2: str, /) -> str:
    return f"{area1} / {area2}"


def idx_cluster(_: str, cluster: str, /) -> str:
    return cluster


def idx_group(group: str, /) -> str:
    return group


# ==========================
#  Scenario Builder Ruleset
# ==========================


def _create_scenarios_mapping(names: Iterable[str], years: list[str]) -> _SimpleScenario:
    return {n: {y: RANDOM for y in years} for n in names}


def _create_cluster_scenarios_mapping(names: Mapping[str, Iterable[str]], years: list[str]) -> _ClusterScenario:
    return {n: _create_scenarios_mapping(cluster_names, years) for n, cluster_names in names.items()}


def _is_cluster(scenario_type: ScenarioType) -> bool:
    return scenario_type in (ScenarioType.THERMAL, ScenarioType.RENEWABLE, ScenarioType.SHORT_TERM_STORAGE_INFLOWS)


@dataclasses.dataclass
class Scenarios:
    load: _SimpleScenario
    thermal: _ClusterScenario
    hydro: _SimpleScenario
    hydro_initial_levels: _SimpleScenario
    hydro_final_levels: _SimpleScenario
    hydro_generation_power: _SimpleScenario
    wind: _SimpleScenario
    solar: _SimpleScenario
    renewable: _ClusterScenario
    short_term_storage_inflows: _ClusterScenario
    binding_constraints: _SimpleScenario
    links: _SimpleScenario

    def get(self, scenario_type: ScenarioType) -> _SimpleScenario | _ClusterScenario | None:
        match scenario_type:
            case ScenarioType.LOAD:
                return self.load
            case ScenarioType.HYDRO:
                return self.hydro
            case ScenarioType.HYDRO_INITIAL_LEVEL:
                return self.hydro_initial_levels
            case ScenarioType.HYDRO_FINAL_LEVEL:
                return self.hydro_final_levels
            case ScenarioType.HYDRO_GENERATION_POWER:
                return self.hydro_generation_power
            case ScenarioType.SOLAR:
                return self.solar
            case ScenarioType.WIND:
                return self.wind
            case ScenarioType.RENEWABLE:
                return self.renewable
            case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
                return self.short_term_storage_inflows
            case ScenarioType.BINDING_CONSTRAINTS:
                return self.binding_constraints
            case ScenarioType.LINK:
                return self.links
            case _:
                raise ValueError(f"Unknown scenario type {scenario_type}")

    def get_cluster(self, scenario_type: ScenarioType) -> _ClusterScenario:
        if not _is_cluster(scenario_type):
            raise ValueError(f"Scenario type {scenario_type} is not a cluster scenario")
        return cast(_ClusterScenario, self.get(scenario_type))

    def get_simple(self, scenario_type: ScenarioType) -> _SimpleScenario:
        if _is_cluster(scenario_type):
            raise ValueError(f"Scenario type {scenario_type} is a cluster scenario")
        return cast(_SimpleScenario, self.get(scenario_type))


class StudyIndex:
    def __init__(
        self,
        areas: Iterable[str],
        links: Iterable[tuple[str, str]],
        thermals: Mapping[str : Iterable[str]],
        storages: Mapping[str, Iterable[str]],
        bc_groups: Iterable[str],
        renewables: Mapping[str, Iterable[str]],
    ):
        to_id = transform_name_to_id
        # TODO: to_id
        self._areas = {a.lower(): a for a in areas}
        self._links = {(a1.lower(), a2.lower()): (a1, a2) for a1, a2 in links}
        self._thermals = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in thermals.items()}
        self._renewables = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in renewables.items()}
        self._storages = {
            a.lower(): {a_storage.lower(): a_storage for a_storage in a_storages} for a, a_storages in storages.items()
        }
        self._bc_groups = {g.lower(): g for g in bc_groups}

    @property
    def area_ids(self) -> Iterable[str]:
        return self._areas.keys()

    def area_name(self, area_id: str) -> str:
        return self._areas[area_id]

    @property
    def thermal_ids(self) -> Mapping[str, Iterable[str]]:
        return self._thermals

    @property
    def renewable_ids(self) -> Mapping[str, Iterable[str]]:
        return self._thermals

    @property
    def bc_group_ids(self) -> Iterable[str]:
        return self._bc_groups

    @property
    def storage_ids(self) -> Mapping[str, Iterable[str]]:
        return self._storages

    @property
    def link_ids(self) -> Iterable[str]:
        return [f"{a1} / {a2}" for a1, a2 in self._links.keys()]


def _create_scenarios(years: list[str], index: StudyIndex) -> Scenarios:
    return Scenarios(
        load=_create_scenarios_mapping(names=index.area_ids, years=years),
        thermal=_create_cluster_scenarios_mapping(names=index.thermal_ids, years=years),
        hydro=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_initial_levels=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_final_levels=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_generation_power=_create_scenarios_mapping(names=index.area_ids, years=years),
        solar=_create_scenarios_mapping(names=index.area_ids, years=years),
        wind=_create_scenarios_mapping(names=index.area_ids, years=years),
        renewable=_create_cluster_scenarios_mapping(names=index.renewable_ids, years=years),
        short_term_storage_inflows=_create_cluster_scenarios_mapping(names=index.storage_ids, years=years),
        binding_constraints=_create_scenarios_mapping(names=index.bc_group_ids, years=years),
        links=_create_scenarios_mapping(names=index.link_ids, years=years),
    )


class RulesetMatrices:
    """
    Scenario Builder Ruleset -- Manage rules of each scenario type as DataFrames.

    This class allows to manage the conversion of data from or to rules in INI format.
    It can also convert the data to a table form (a dictionary of dictionaries) for the frontend.
    """

    def __init__(
        self,
        *,
        nb_years: int,
        areas: Iterable[str],
        links: Iterable[Tuple[str, str]],
        thermals: Mapping[str, Iterable[str]],
        renewables: Mapping[str, Iterable[str]],
        groups: Iterable[str],
        storages: Mapping[str, Iterable[str]],
        scenario_types: Optional[Mapping[str, str]] = None,
    ):
        # List of Monte Carlo years
        self.columns = [str(i) for i in range(nb_years)]
        # Dictionaries used to manage case insensitivity

        self.scenario_types = scenario_types or SCENARIO_TYPES
        self.index = StudyIndex(
            areas=areas, thermals=thermals, links=links, renewables=renewables, storages=storages, bc_groups=groups
        )
        # Dictionary used to store the scenario matrices
        self.scenarios: Scenarios = _create_scenarios(index=self.index, years=self.columns)

    def update_rules(self, rules: Mapping[str, _Value]) -> None:
        """
        Update the scenario matrices with the given rules read from an INI file.

        Args:
            rules: Dictionary of rules with the following format

                ::

                    {
                        "symbol,area_id,year": value,  # load, hydro, wind, solar...
                        "symbol,area1_id,area2_id,year": value,  # links
                        "symbol,area_id,cluster_id,year": value,  # thermal and renewable clusters
                        "symbol,group_id,year": value,  # binding constraints
                    }
        """
        for key, value in rules.items():
            symbol, *parts = key.split(",")
            scenario_type = self.scenario_types[symbol]
            match scenario_type:
                case ScenarioType.LOAD:
                    area_id, year = parts
                    self.scenarios.load[area_id][year] = value
                case ScenarioType.THERMAL:
                    area_id, year, cluster_id = parts
                    self.scenarios.thermal[area_id][cluster_id][year] = value
                case ScenarioType.HYDRO:
                    area_id, year = parts
                    self.scenarios.hydro[area_id][year] = value
                case ScenarioType.HYDRO_INITIAL_LEVEL:
                    area_id, year = parts
                    self.scenarios.hydro_initial_levels[area_id][year] = value * 100
                case ScenarioType.HYDRO_FINAL_LEVEL:
                    area_id, year = parts
                    self.scenarios.hydro_initial_levels[area_id][year] = value * 100
                case ScenarioType.HYDRO_GENERATION_POWER:
                    area_id, year = parts
                    self.scenarios.hydro_initial_levels[area_id][year] = value
                case ScenarioType.LINK:
                    area1, area2, year = parts
                    self.scenarios.links[f"{area1} / {area2}"][year] = value
                case ScenarioType.SOLAR:
                    area_id, year = parts
                    self.scenarios.solar[area_id][year] = value
                case ScenarioType.WIND:
                    area_id, year = parts
                    self.scenarios.wind[area_id][year] = value
                case ScenarioType.RENEWABLE:
                    area_id, year, cluster_id = parts
                    self.scenarios.renewable[area_id][cluster_id][year] = value
                case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
                    area_id, year, storage_id = parts
                    self.scenarios.short_term_storage_inflows[area_id][storage_id][year] = value
                case ScenarioType.BINDING_CONSTRAINTS:
                    group_id, year = parts
                    self.scenarios.binding_constraints[group_id][year] = value
                case _:
                    raise NotImplementedError(f"Unknown symbol {symbol}")

    def get_rules(self, *, allow_nan: bool = False) -> Dict[str, _Value]:
        """
        Get the rules from the scenario matrices in INI format.

        Args:
            allow_nan: Allow NaN values if True.

        Returns:
            Dictionary of rules with the following format

            ::

                {
                    "symbol,area_id,year": value,  # load, hydro, wind, solar...
                    "symbol,area1_id,area2_id,year": value,  # links
                    "symbol,area_id,cluster_id,year": value,  # thermal and renewable clusters
                    "symbol,group_id,year": value,  # binding constraints
                }
        """
        rules: Dict[str, _Value] = {}
        for symbol, scenario_type in self.scenario_types.items():
            scenario = self.scenarios.get(scenario_type)
            scenario_rules = self.get_scenario_rules(scenario, symbol, allow_nan=allow_nan)
            rules.update(scenario_rules)
        return rules

    def get_scenario_rules(self, scenario: _Scenario, symbol: str, *, allow_nan: bool = False) -> Dict[str, _Value]:
        """
        Get the rules for a specific scenario matrix and symbol.

        Args:
            scenario: Matrix or dictionary of matrices.
            symbol: Rule symbol.
            allow_nan: Allow NaN values if True.

        Returns:
            Dictionary of rules.
        """

        def to_ts_number(v: Any) -> _Value:
            """Convert value to TimeSeries number."""
            return np.nan if pd.isna(v) else int(v)

        def to_percent(v: Any) -> _Value:
            """Convert value to percentage in range [0, 100]."""
            return np.nan if pd.isna(v) else float(v) / 100

        if symbol in _AREA_RELATED_SYMBOLS:
            scenario_rules = {
                f"{symbol},{area_id},{year}": to_ts_number(value)
                for area_id, area in self.areas.items()
                for year, value in scenario.loc[idx_area(area)].items()  # type: ignore
                if allow_nan or not pd.isna(value)
            }
        elif symbol in _LINK_RELATED_SYMBOLS:
            scenario_rules = {
                f"{symbol},{area1_id},{area2_id},{year}": to_ts_number(value)
                for (area1_id, area2_id), (area1, area2) in self.links.items()
                for year, value in scenario.loc[idx_link(area1, area2)].items()  # type: ignore
                if allow_nan or not pd.isna(value)
            }
        elif symbol in _HYDRO_LEVEL_RELATED_SYMBOLS:
            scenario_rules = {
                f"{symbol},{area_id},{year}": to_percent(value)
                for area_id, area in self.areas.items()
                for year, value in scenario.loc[idx_area(area)].items()  # type: ignore
                if allow_nan or not pd.isna(value)
            }
        elif symbol in _CLUSTER_RELATED_SYMBOLS:
            clusters_mapping = self.clusters_by_symbols[symbol]
            scenario = cast(_ClusterScenario, scenario)
            scenario_rules = {
                f"{symbol},{area_id},{year},{cluster_id}": to_ts_number(value)
                for area_id, clusters in clusters_mapping.items()
                for cluster_id, cluster in clusters.items()
                for year, value in scenario[self.areas[area_id]][idx_cluster(self.areas[area_id], cluster)].items()
                if allow_nan or not pd.isna(value)
            }
        elif symbol in _BINDING_CONSTRAINTS_RELATED_SYMBOLS:
            scenario_rules = {
                f"{symbol},{group_id},{year}": to_ts_number(value)
                for group_id, group in self.groups.items()
                for year, value in scenario.loc[idx_group(group)].items()  # type: ignore
                if allow_nan or not pd.isna(value)
            }
        else:
            raise NotImplementedError(f"Unknown symbol {symbol}")
        return scenario_rules

    def get_table_form(self, scenario_type: str) -> TableForm:
        """
        Get the scenario matrices in table form for the frontend.

        Args:
            scenario_type: Scenario type.

        Returns:
            Dictionary of dictionaries with the following format

            ::

                {
                    "area_id": {
                        "year": value,
                        ...
                    },
                    ...
                }

            For thermal and renewable clusters, the dictionary is nested:

            ::

                {
                    "area_id": {
                        "cluster_id": {
                            "year": value,
                            ...
                        },
                        ...
                    },
                    ...
                }
        """
        return self.scenarios[scenario_type]

    def update_table_form(self, table_form: TableForm, scenario_type: str, *, nan_value: str = "") -> None:
        """
        Update the scenario matrices from table form data (partial update).

        Args:
            table_form: Simple or cluster table form data (see :meth:`get_table_form` for the format).
            scenario_type: Scenario type.
            nan_value: Value to replace NaNs. for instance: ``{"& psp x1": {"0": 10}}``.
        """
        scenario = self.scenarios[scenario_type]
        if isinstance(scenario, pd.DataFrame):
            # Simple (non-clustered) scenario: update the main DataFrame directly
            simple_table_form = cast(SimpleTableForm, table_form)
            df = pd.DataFrame.from_dict(simple_table_form, orient="index").replace({None: np.nan, nan_value: np.nan})
            scenario.loc[df.index, df.columns] = df
        else:
            # Clustered scenario: update each area's DataFrame individually
            cluster_table_form = cast(ClusterTableForm, table_form)
            for area, simple_table_form in cluster_table_form.items():
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type][area])
                df = pd.DataFrame(simple_table_form).transpose().replace({None: np.nan, nan_value: np.nan})
                scenario.loc[df.index, df.columns] = df
