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

import enum
from typing import Any, Dict, Mapping, MutableMapping, cast

import typing_extensions as te
from typing_extensions import override

from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.ruleset_matrices import RulesetMatrices, TableForm
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# Symbols used in scenario builder data
_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "bc", "hgp"
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r"

_HYDRO_LEVEL_PERCENT = 100

_Section: te.TypeAlias = MutableMapping[str, int | float]
_Sections: te.TypeAlias = MutableMapping[str, _Section]

Ruleset: te.TypeAlias = MutableMapping[str, Any]
Rulesets: te.TypeAlias = MutableMapping[str, Ruleset]


class ScenarioType(enum.StrEnum):
    """
    Scenario type

    - LOAD: Load scenario
    - THERMAL: Thermal cluster scenario
    - HYDRO: Hydraulic scenario
    - WIND: Wind scenario
    - SOLAR: Solar scenario
    - NTC: NTC scenario (link)
    - RENEWABLE: Renewable scenario
    - BINDING_CONSTRAINTS: Binding constraints scenario
    - HYDRO_INITIAL_LEVEL: hydraulic Initial level scenario
    - HYDRO_FINAL_LEVEL: hydraulic Final level scenario
    - HYDRO_GENERATION_POWER: hydraulic Generation power scenario
    """

    LOAD = "load"
    THERMAL = "thermal"
    HYDRO = "hydro"
    WIND = "wind"
    SOLAR = "solar"
    LINK = "ntc"
    RENEWABLE = "renewable"
    BINDING_CONSTRAINTS = "bindingConstraints"
    HYDRO_INITIAL_LEVEL = "hydroInitialLevels"
    HYDRO_FINAL_LEVEL = "hydroFinalLevels"
    HYDRO_GENERATION_POWER = "hydroGenerationPower"

    @override
    def __str__(self) -> str:
        """Return the string representation of the enum value."""
        return self.value


SYMBOLS_BY_SCENARIO_TYPES = {
    ScenarioType.LOAD: "l",
    ScenarioType.HYDRO: "h",
    ScenarioType.WIND: "w",
    ScenarioType.SOLAR: "s",
    ScenarioType.THERMAL: "t",
    ScenarioType.RENEWABLE: "r",
    ScenarioType.LINK: "ntc",
    ScenarioType.BINDING_CONSTRAINTS: "bc",
    ScenarioType.HYDRO_INITIAL_LEVEL: "hl",
    ScenarioType.HYDRO_FINAL_LEVEL: "hfl",
    ScenarioType.HYDRO_GENERATION_POWER: "hgp",
}


def _get_ruleset_config(
    file_study: FileStudy,
    ruleset_name: str,
    symbol: str = "",
) -> Dict[str, int | float]:
    try:
        suffix = f"/{symbol}" if symbol else ""
        url = f"settings/scenariobuilder/{ruleset_name}{suffix}".split("/")
        ruleset_cfg = cast(Dict[str, int | float], file_study.tree.get(url))
    except KeyError:
        ruleset_cfg = {}
    return ruleset_cfg


def _get_nb_years(file_study: FileStudy) -> int:
    try:
        # noinspection SpellCheckingInspection
        url = "settings/generaldata/general/nbyears".split("/")
        nb_years = cast(int, file_study.tree.get(url))
    except KeyError:
        nb_years = 1
    return nb_years


def _get_active_ruleset_name(file_study: FileStudy, default_ruleset: str = "Default Ruleset") -> str:
    """
    Get the active ruleset name stored in the configuration at the following path:
    ``settings/generaldata.ini``, in the section "general", key "active-rules-scenario".

    This ruleset name must match a section name in the scenario builder configuration
    at the following path: ``settings/scenariobuilder``.

    Args:
        file_study: Object representing the study file
        default_ruleset: Name of the default ruleset

    Returns:
        The active ruleset name if found in the configuration, or the default ruleset name if missing.
    """
    try:
        url = "settings/generaldata/general/active-rules-scenario".split("/")
        active_ruleset = cast(str, file_study.tree.get(url))
    except KeyError:
        active_ruleset = default_ruleset
    else:
        # In some old studies, the active ruleset is stored in lowercase.
        if not active_ruleset or active_ruleset.lower() == "default ruleset":
            active_ruleset = default_ruleset
    return active_ruleset


def _build_ruleset(file_study: FileStudy, symbol: str = "") -> RulesetMatrices:
    ruleset_name = _get_active_ruleset_name(file_study)
    nb_years = _get_nb_years(file_study)
    ruleset_config = _get_ruleset_config(file_study, ruleset_name, symbol)

    # Create and populate the RulesetMatrices
    areas = file_study.config.areas
    groups = file_study.config.get_binding_constraint_groups() if file_study.config.version >= 870 else []
    scenario_types = {s: str(st) for st, s in SYMBOLS_BY_SCENARIO_TYPES.items()}
    ruleset = RulesetMatrices(
        nb_years=nb_years,
        areas=areas,
        links=((a1, a2) for a1 in areas for a2 in file_study.config.get_links(a1)),
        thermals={a: file_study.config.get_thermal_ids(a) for a in areas},
        renewables={a: file_study.config.get_renewable_ids(a) for a in areas},
        groups=groups,
        scenario_types=scenario_types,
    )
    ruleset.update_rules(ruleset_config)
    return ruleset


class ScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_config(self, study: StudyInterface) -> Rulesets:
        sections = cast(_Sections, study.get_files().tree.get(["settings", "scenariobuilder"]))

        rulesets: Rulesets = {}
        for ruleset_name, data in sections.items():
            ruleset = rulesets.setdefault(ruleset_name, {})
            for key, value in data.items():
                symbol, *parts = key.split(",")
                scenario = ruleset.setdefault(symbol, {})
                if symbol in _AREA_RELATED_SYMBOLS:
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area[parts[1]] = int(value)
                elif symbol in _HYDRO_LEVEL_RELATED_SYMBOLS:
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area[parts[1]] = float(value) * _HYDRO_LEVEL_PERCENT
                elif symbol in _LINK_RELATED_SYMBOLS:
                    scenario_link = scenario.setdefault(f"{parts[0]} / {parts[1]}", {})
                    scenario_link[parts[2]] = int(value)
                elif symbol in _CLUSTER_RELATED_SYMBOLS:
                    scenario_area = scenario.setdefault(parts[0], {})
                    scenario_area_cluster = scenario_area.setdefault(parts[2], {})
                    scenario_area_cluster[parts[1]] = int(value)
                else:  # pragma: no cover
                    raise NotImplementedError(f"Unknown symbol {symbol}")

        return rulesets

    def update_config(self, study: StudyInterface, rulesets: Rulesets) -> None:

        sections: _Sections = {}
        for ruleset_name, ruleset in rulesets.items():
            section = sections[ruleset_name] = {}
            for symbol, data in ruleset.items():
                if symbol in _AREA_RELATED_SYMBOLS:
                    _populate_common(section, symbol, data)
                elif symbol in _HYDRO_LEVEL_RELATED_SYMBOLS:
                    _populate_hydro_levels(section, symbol, data)
                elif symbol in _LINK_RELATED_SYMBOLS:
                    _populate_links(section, symbol, data)
                elif symbol in _CLUSTER_RELATED_SYMBOLS:
                    _populate_clusters(section, symbol, data)
                else:  # pragma: no cover
                    raise NotImplementedError(f"Unknown symbol {symbol}")

        command = UpdateScenarioBuilder(
            data=sections, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])

    def get_scenario_by_type(self, study: StudyInterface, scenario_type: ScenarioType) -> TableForm:
        symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
        file_study = study.get_files()
        ruleset = _build_ruleset(file_study, symbol)
        ruleset.sort_scenarios()

        # Extract the table form for the given scenario type
        table_form = ruleset.get_table_form(str(scenario_type), nan_value="")
        return table_form

    def update_scenario_by_type(
        self, study: StudyInterface, table_form: TableForm, scenario_type: ScenarioType
    ) -> TableForm:
        file_study = study.get_files()
        ruleset = _build_ruleset(file_study)
        ruleset.update_table_form(table_form, str(scenario_type), nan_value="")
        ruleset.sort_scenarios()

        # Create the UpdateScenarioBuilder command
        ruleset_name = _get_active_ruleset_name(file_study)
        data = {ruleset_name: ruleset.get_rules(allow_nan=True)}
        update_scenario = UpdateScenarioBuilder(
            data=data, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([update_scenario])

        # Extract the updated table form for the given scenario type
        table_form = ruleset.get_table_form(str(scenario_type), nan_value="")
        return table_form


def _populate_common(section: _Section, symbol: str, data: Mapping[str, Mapping[str, Any]]) -> None:
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            section[f"{symbol},{area},{year}"] = value


def _populate_hydro_levels(section: _Section, symbol: str, data: Mapping[str, Mapping[str, Any]]) -> None:
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            if isinstance(value, (int, float)) and value != float("nan"):
                value /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = value


def _populate_links(section: _Section, symbol: str, data: Mapping[str, Mapping[str, Any]]) -> None:
    for link, scenario_link in data.items():
        for year, value in scenario_link.items():
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _populate_clusters(section: _Section, symbol: str, data: Mapping[str, Mapping[str, Any]]) -> None:
    for area, scenario_area in data.items():
        for cluster, scenario_area_cluster in scenario_area.items():
            for year, value in scenario_area_cluster.items():
                section[f"{symbol},{area},{year},{cluster}"] = value
