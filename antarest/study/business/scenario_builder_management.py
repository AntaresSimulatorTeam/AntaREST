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

from typing import cast

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Ruleset,
    Rulesets,
    ScenarioType,
    initialize_ruleset,
    study_index,
    update_ruleset,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    RulesetsFileData,
    extract_ruleset_data,
    parse_ruleset,
    parse_rulesets,
    serialize_ruleset,
    serialize_rulesets,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext


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


def _read_ruleset(file_study: FileStudy, scenario_type: ScenarioType) -> Ruleset:
    ruleset_name = _get_active_ruleset_name(file_study)
    nb_years = _get_nb_years(file_study)
    ruleset_config = extract_ruleset_data(file_study, ruleset_name, scenario_type)

    complete_ruleset = initialize_ruleset(
        years=[str(y) for y in range(1, nb_years + 1)],
        index=study_index(file_study.tree),
        scenario_types={scenario_type},
    )
    file_ruleset = parse_ruleset(ruleset_config)
    update_ruleset(complete_ruleset, file_ruleset)
    return complete_ruleset


class ScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_config(self, study: StudyInterface) -> Rulesets:
        sections = cast(RulesetsFileData, study.get_files().tree.get(["settings", "scenariobuilder"]))
        return parse_rulesets(sections)

    def update_config(self, study: StudyInterface, rulesets: Rulesets) -> None:
        sections: RulesetsFileData = serialize_rulesets(rulesets)

        command = UpdateScenarioBuilder(
            data=sections, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])

    def get_scenario_by_type(self, study: StudyInterface, scenario_type: ScenarioType) -> AnyScenarios:
        file_study = study.get_files()
        ruleset = _read_ruleset(file_study, scenario_type)

        # Extract the table form for the given scenario type
        return ruleset.get(scenario_type)

    def update_scenario_by_type(
        self, study: StudyInterface, table_form: AnyScenarios, scenario_type: ScenarioType
    ) -> AnyScenarios:
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
