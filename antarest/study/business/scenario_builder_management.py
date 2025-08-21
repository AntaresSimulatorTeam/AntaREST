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

from typing import Dict, cast

from antarest.study.business.model.scenario_builder_model import (
    GenericScenarios,
    Ruleset,
    Rulesets,
    ScenarioType,
    initialize_ruleset,
    study_index,
    update_ruleset,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    RulesetsSections,
    parse_ruleset,
    parse_rulesets,
    serialize_ruleset,
    serialize_rulesets,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# Maps MC year to TS number
# Maps MC year to level value

# A link ID is "area1 / area2"


_SCENARIO_TYPE_NAMES = {
    ScenarioType.LOAD: "load",
    ScenarioType.HYDRO: "hydro",
    ScenarioType.WIND: "wind",
    ScenarioType.SOLAR: "solar",
    ScenarioType.THERMAL: "thermal",
    ScenarioType.RENEWABLE: "renewable",
    ScenarioType.LINK: "link",
    ScenarioType.BINDING_CONSTRAINTS: "binding-constraints",
    ScenarioType.HYDRO_INITIAL_LEVEL: "hydro-initial-levels",
    ScenarioType.HYDRO_FINAL_LEVEL: "hydro-final-levels",
    ScenarioType.HYDRO_GENERATION_POWER: "hydro-generation-power",
    ScenarioType.SHORT_TERM_STORAGE_INFLOWS: "short-term-storage-inflows",
}

# We may have multiple rulesets, each with its own name

_SCENARIO_TYPE_SYMBOLS = {
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
}


def _get_ruleset_config(
    file_study: FileStudy,
    ruleset_name: str,
    symbol: str,
) -> Dict[str, int | float]:
    try:
        suffix = f"/{symbol}"
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


def _build_ruleset(file_study: FileStudy, symbol: str) -> Ruleset:
    ruleset_name = _get_active_ruleset_name(file_study)
    nb_years = _get_nb_years(file_study)
    ruleset_config = _get_ruleset_config(file_study, ruleset_name, symbol)
    complete_ruleset = initialize_ruleset(
        years=[str(y) for y in range(1, nb_years + 1)], index=study_index(file_study.tree)
    )
    file_ruleset = parse_ruleset(ruleset_config)
    update_ruleset(complete_ruleset, file_ruleset)
    return complete_ruleset


class ScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_config(self, study: StudyInterface) -> Rulesets:
        sections = cast(RulesetsSections, study.get_files().tree.get(["settings", "scenariobuilder"]))
        return parse_rulesets(sections)

    def update_config(self, study: StudyInterface, rulesets: Rulesets) -> None:
        sections: RulesetsSections = serialize_rulesets(rulesets)

        command = UpdateScenarioBuilder(
            data=sections, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])

    def get_scenario_by_type(self, study: StudyInterface, scenario_type: ScenarioType) -> GenericScenarios:
        symbol = _SCENARIO_TYPE_SYMBOLS[scenario_type]
        file_study = study.get_files()
        ruleset = _build_ruleset(file_study, symbol)

        # Extract the table form for the given scenario type
        return ruleset.get(scenario_type)

    def update_scenario_by_type(
        self, study: StudyInterface, table_form: GenericScenarios, scenario_type: ScenarioType
    ) -> GenericScenarios:
        file_study = study.get_files()
        ruleset_update = Ruleset()
        ruleset_update.set(scenario_type, table_form)

        # Create the UpdateScenarioBuilder command
        ruleset_name = _get_active_ruleset_name(file_study)
        serialized_ruleset = serialize_ruleset(ruleset_update)
        data = {ruleset_name: serialized_ruleset}
        update_scenario = UpdateScenarioBuilder(
            data=data, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([update_scenario])

        # Extract the updated table form for the given scenario type
        ruleset = self.get_config(study)[ruleset_name]
        update_ruleset(ruleset, ruleset_update)
        return ruleset.get(scenario_type)
