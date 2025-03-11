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

from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple, cast

import numpy as np
import pandas as pd
import typing_extensions as te
from typing_extensions import override

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
}

_Value: te.TypeAlias = int | float
_SimpleScenario: te.TypeAlias = pd.DataFrame
_ClusterScenario: te.TypeAlias = MutableMapping[str, pd.DataFrame]
_Scenario: te.TypeAlias = _SimpleScenario | _ClusterScenario
_ScenarioMapping: te.TypeAlias = MutableMapping[str, _Scenario]

SimpleTableForm: te.TypeAlias = Dict[str, Dict[str, int | float | str | None]]
ClusterTableForm: te.TypeAlias = Dict[str, SimpleTableForm]
TableForm: te.TypeAlias = SimpleTableForm | ClusterTableForm

_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "hgp"
_BINDING_CONSTRAINTS_RELATED_SYMBOLS = ("bc",)
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r"


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
        scenario_types: Optional[Mapping[str, str]] = None,
    ):
        # List of Monte Carlo years
        self.columns = [str(i) for i in range(nb_years)]
        # Dictionaries used to manage case insensitivity
        self.areas = {a.lower(): a for a in areas}
        self.links = {(a1.lower(), a2.lower()): (a1, a2) for a1, a2 in links}
        self.thermals = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in thermals.items()}
        self.renewables = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in renewables.items()}
        self.clusters_by_symbols = {"t": self.thermals, "r": self.renewables}  # for easier access
        self.groups = {g.lower(): g for g in groups}
        # Dictionary used to convert symbols to scenario types
        self.scenario_types = scenario_types or SCENARIO_TYPES
        # Dictionary used to store the scenario matrices
        self.scenarios: _ScenarioMapping = {}
        self._setup()

    @override
    def __str__(self) -> str:
        lines = []
        for symbol, scenario_type in self.scenario_types.items():
            lines.append(f"# {scenario_type}")
            scenario = self.scenarios[scenario_type]
            if isinstance(scenario, pd.DataFrame):
                lines.append(scenario.to_string())
                lines.append("")
            else:
                for area, scenario in scenario.items():
                    lines.append(f"## {scenario_type} in {area}")
                    lines.append(scenario.to_string())
                    lines.append("")
        return "\n".join(lines)

    def get_area_index(self) -> List[str]:
        return [idx_area(area) for area in self.areas.values()]

    def get_link_index(self) -> List[str]:
        return [idx_link(a1, a2) for a1, a2 in self.links.values()]

    def get_cluster_index(self, symbol: str, area: str) -> List[str]:
        clusters = self.clusters_by_symbols[symbol][area.lower()]
        return [idx_cluster(area, cluster) for cluster in clusters.values()]

    def get_group_index(self) -> List[str]:
        return [idx_group(group) for group in self.groups.values()]

    def _setup(self) -> None:
        """
        Prepare the scenario matrices for each scenario type.
        """
        area_index = self.get_area_index()
        group_index = self.get_group_index()
        link_index = self.get_link_index()
        for symbol, scenario_type in self.scenario_types.items():
            # Note: all DataFrames are initialized with NaN values, so the dtype is `float`.
            if symbol in _AREA_RELATED_SYMBOLS:
                self.scenarios[scenario_type] = pd.DataFrame(index=area_index, columns=self.columns, dtype=float)
            elif symbol in _BINDING_CONSTRAINTS_RELATED_SYMBOLS:
                self.scenarios[scenario_type] = pd.DataFrame(index=group_index, columns=self.columns, dtype=float)
            elif symbol in _LINK_RELATED_SYMBOLS:
                self.scenarios[scenario_type] = pd.DataFrame(index=link_index, columns=self.columns, dtype=float)
            elif symbol in _HYDRO_LEVEL_RELATED_SYMBOLS:
                self.scenarios[scenario_type] = pd.DataFrame(index=area_index, columns=self.columns, dtype=float)
            elif symbol in _CLUSTER_RELATED_SYMBOLS:
                # We only take the areas that are defined in the thermals and renewables dictionaries
                # Keys are the names of the areas (and not the identifiers)
                self.scenarios[scenario_type] = {
                    self.areas[area_id]: pd.DataFrame(
                        index=self.get_cluster_index(symbol, self.areas[area_id]), columns=self.columns, dtype=float
                    )
                    for area_id, cluster in self.clusters_by_symbols[symbol].items()
                    if cluster
                }
            else:
                raise NotImplementedError(f"Unknown symbol {symbol}")

    def sort_scenarios(self) -> None:
        """
        Sort the indexes of the scenario matrices (case-insensitive).
        """
        for symbol, scenario_type in self.scenario_types.items():
            scenario = self.scenarios[scenario_type]
            if isinstance(scenario, pd.DataFrame):
                scenario = scenario.sort_index(key=lambda x: x.str.lower())
            else:
                scenario = {area: df.sort_index(key=lambda x: x.str.lower()) for area, df in scenario.items()}
            self.scenarios[scenario_type] = scenario

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
            # Common values
            area_id = parts[0].lower()  # or group_id for BC
            year = parts[2] if symbol in _LINK_RELATED_SYMBOLS else parts[1]
            if symbol in _AREA_RELATED_SYMBOLS:
                area = self.areas[area_id]
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type])
                scenario.at[idx_area(area), str(year)] = value
            elif symbol in _LINK_RELATED_SYMBOLS:
                area1 = self.areas[area_id]
                area2 = self.areas[parts[1].lower()]
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type])
                scenario.at[idx_link(area1, area2), str(year)] = value
            elif symbol in _HYDRO_LEVEL_RELATED_SYMBOLS:
                area = self.areas[area_id]
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type])
                scenario.at[idx_area(area), str(year)] = value * 100
            elif symbol in _CLUSTER_RELATED_SYMBOLS:
                area = self.areas[area_id]
                clusters = self.clusters_by_symbols[symbol][area_id]
                cluster = clusters[parts[2].lower()]
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type][area])
                scenario.at[idx_cluster(area, cluster), str(year)] = value
            elif symbol in _BINDING_CONSTRAINTS_RELATED_SYMBOLS:
                group = self.groups[area_id]
                scenario = cast(pd.DataFrame, self.scenarios[scenario_type])
                scenario.at[idx_group(group), str(year)] = value
            else:
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
            scenario = self.scenarios[scenario_type]
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
            scenario_rules = {
                f"{symbol},{area_id},{year},{cluster_id}": to_ts_number(value)
                for area_id, clusters in clusters_mapping.items()
                for cluster_id, cluster in clusters.items()
                for year, value in scenario[self.areas[area_id]].loc[idx_cluster(self.areas[area_id], cluster)].items()
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

    def get_table_form(self, scenario_type: str, *, nan_value: str | None = "") -> TableForm:
        """
        Get the scenario matrices in table form for the frontend.

        Args:
            scenario_type: Scenario type.
            nan_value: Value to replace NaNs.

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
        scenario = self.scenarios[scenario_type]
        if isinstance(scenario, pd.DataFrame):
            simple_scenario: _SimpleScenario = scenario.fillna(nan_value)
            simple_table_form = simple_scenario.to_dict(orient="index")
            return cast(SimpleTableForm, simple_table_form)
        else:
            cluster_scenario: _ClusterScenario = {area: df.fillna(nan_value) for area, df in scenario.items()}
            cluster_table_form = {area: df.to_dict(orient="index") for area, df in cluster_scenario.items()}
            return cast(ClusterTableForm, cluster_table_form)

    def set_table_form(
        self,
        table_form: TableForm,
        scenario_type: str,
        *,
        nan_value: str | None = "",
    ) -> None:
        """
        Set the scenario matrix from table form data, for a specific scenario type.

        Args:
            table_form: Simple or cluster table form data (see :meth:`get_table_form` for the format).
            scenario_type: Scenario type.
            nan_value: Value to replace NaNs.
        """
        actual_scenario = self.scenarios[scenario_type]
        if isinstance(actual_scenario, pd.DataFrame):
            scenario = pd.DataFrame.from_dict(table_form, orient="index")
            scenario = scenario.replace({None: np.nan, nan_value: np.nan})
            self.scenarios[scenario_type] = scenario
        else:
            self.scenarios[scenario_type] = {
                area: pd.DataFrame.from_dict(df, orient="index").replace({None: np.nan, nan_value: np.nan})
                for area, df in table_form.items()
            }

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
            simple_table_form = t.cast(SimpleTableForm, table_form)
            df = pd.DataFrame.from_dict(simple_table_form, orient="index").replace({None: np.nan, nan_value: np.nan})
            scenario.loc[df.index, df.columns] = df
        else:
            cluster_table_form = cast(ClusterTableForm, table_form)
            for area, simple_table_form in cluster_table_form.items():
                scenario = t.cast(pd.DataFrame, self.scenarios[scenario_type][area])
                df = pd.DataFrame(simple_table_form).transpose().replace({None: np.nan, nan_value: np.nan})
                scenario.loc[df.index, df.columns] = df
