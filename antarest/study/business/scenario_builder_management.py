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
from typing import Any, Dict, MutableMapping, TypeAlias, cast

from pydantic import Field, TypeAdapter
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.ruleset_matrices import RulesetMatrices, TableForm
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# Symbols used in scenario builder data
_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "bc", "hgp"
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r", "sts"

_HYDRO_LEVEL_PERCENT = 100

_Section: TypeAlias = MutableMapping[str, int | float]
_Sections: TypeAlias = MutableMapping[str, _Section]


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
    - SHORT_TERM_STORAGE_INFLOWS: Short term storage inflows scenario
    - SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS: Short term storage additional constraints scenario

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
    SHORT_TERM_STORAGE_INFLOWS = "shortTermStorageInflows"
    SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS = "shortTermStorageAdditionalConstraints"

    @override
    def __str__(self) -> str:
        """Return the string representation of the enum value."""
        return self.value


AreaId: TypeAlias = str
LinkId: TypeAlias = str
ObjectId: TypeAlias = str
ConstraintId: TypeAlias = str

# Maps MC year to TS number
McYearToTimeSeries: TypeAlias = dict[str, int]
# Maps MC year to level value
McYearToValue: TypeAlias = dict[str, int]

AreaScenarios: TypeAlias = dict[AreaId, McYearToTimeSeries]
# A link ID is "area1 / area2"
LinkScenarios: TypeAlias = dict[LinkId, McYearToTimeSeries]
AreaItemsScenarios: TypeAlias = dict[AreaId, dict[ObjectId, McYearToTimeSeries]]
AdditionalConstraintScenarios: TypeAlias = dict[AreaId, dict[ObjectId, dict[ConstraintId, McYearToTimeSeries]]]
HydroLevelsScenarios: TypeAlias = dict[AreaId, McYearToValue]


class Ruleset(AntaresBaseModel):
    load: AreaScenarios | None = Field(default=None, alias="l")
    thermal: AreaItemsScenarios | None = Field(default=None, alias="t")
    hydro: AreaScenarios | None = Field(default=None, alias="h")
    hydro_initial_levels: HydroLevelsScenarios | None = Field(default=None, alias="hl")
    hydro_final_levels: HydroLevelsScenarios | None = Field(default=None, alias="hfl")
    hydro_generation_power: AreaScenarios | None = Field(default=None, alias="hgp")
    wind: AreaScenarios | None = Field(default=None, alias="w")
    solar: AreaScenarios | None = Field(default=None, alias="s")
    ntc: AreaScenarios | None = Field(default=None, alias="ntc")
    renewable: AreaItemsScenarios | None = Field(default=None, alias="r")
    binding_constraints: AreaScenarios | None = Field(default=None, alias="bc")
    short_term_storage_inflows: AreaItemsScenarios | None = Field(default=None, alias="sts")


# We may have multiple rulesets, each with its own name
Rulesets: TypeAlias = dict[str, Ruleset]

_RULESETS_ADAPTER: TypeAdapter[Rulesets] = TypeAdapter(Rulesets)

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
    ScenarioType.SHORT_TERM_STORAGE_INFLOWS: "sts",
    ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS: "sta",
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
        storages={a: file_study.config.get_st_storage_ids(a) for a in areas},
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

        rulesets: dict[str, Any] = {}
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

        return _RULESETS_ADAPTER.validate_python(rulesets)

    def update_config(self, study: StudyInterface, rulesets: Rulesets) -> None:
        sections: _Sections = {}
        for ruleset_name, ruleset in rulesets.items():
            section = sections[ruleset_name] = {}
            _populate_common(section, ScenarioType.LOAD, ruleset.load)
            _populate_clusters(section, ScenarioType.THERMAL, ruleset.thermal)
            _populate_common(section, ScenarioType.HYDRO, ruleset.hydro)
            _populate_hydro_levels(section, ScenarioType.HYDRO_INITIAL_LEVEL, ruleset.hydro_initial_levels)
            _populate_hydro_levels(section, ScenarioType.HYDRO_FINAL_LEVEL, ruleset.hydro_final_levels)
            _populate_common(section, ScenarioType.HYDRO_GENERATION_POWER, ruleset.hydro_generation_power)
            _populate_common(section, ScenarioType.WIND, ruleset.wind)
            _populate_common(section, ScenarioType.SOLAR, ruleset.solar)
            _populate_links(section, ScenarioType.LINK, ruleset.ntc)
            _populate_clusters(section, ScenarioType.RENEWABLE, ruleset.renewable)
            _populate_common(section, ScenarioType.BINDING_CONSTRAINTS, ruleset.binding_constraints)
            _populate_clusters(section, ScenarioType.SHORT_TERM_STORAGE_INFLOWS, ruleset.short_term_storage_inflows)

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


def _populate_common(section: _Section, scenario_type: ScenarioType, data: AreaScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            section[f"{symbol},{area},{year}"] = value


def _populate_hydro_levels(section: _Section, scenario_type: ScenarioType, data: HydroLevelsScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            val: int | float = value
            if isinstance(value, (int, float)) and value != float("nan"):
                val /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = val


def _populate_links(section: _Section, scenario_type: ScenarioType, data: AreaScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for link, scenario_link in data.items():
        for year, value in scenario_link.items():
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _populate_clusters(section: _Section, scenario_type: ScenarioType, data: AreaItemsScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for cluster, scenario_area_cluster in scenario_area.items():
            for year, value in scenario_area_cluster.items():
                section[f"{symbol},{area},{year},{cluster}"] = value
