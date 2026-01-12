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

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Rulesets,
    RulesetsUpdate,
    RulesetUpdate,
    ScenarioType,
    update_ruleset,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_rulesets(self, study: StudyInterface) -> Rulesets:
        return study.get_study_dao().get_rulesets()

    def update_scenario(self, study: StudyInterface, rulesets: RulesetsUpdate) -> None:
        command = UpdateScenarioBuilder(
            data=rulesets, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])

    def get_scenario_by_type(self, study: StudyInterface, scenario_type: ScenarioType) -> AnyScenarios:
        return study.get_study_dao().get_scenario_by_type(scenario_type)

    def update_scenario_by_type(
        self, study: StudyInterface, scenarios: AnyScenarios, scenario_type: ScenarioType
    ) -> AnyScenarios:
        ruleset_update = RulesetUpdate()
        ruleset_update.set(scenario_type, scenarios)

        # Create the UpdateScenarioBuilder command
        ruleset_name = study.get_study_dao().get_active_ruleset_name()
        data = {ruleset_name: ruleset_update}

        update_scenario = UpdateScenarioBuilder(
            data=data, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([update_scenario])

        # Extract the updated table form for the given scenario type
        ruleset = self.get_rulesets(study)[ruleset_name]
        update_ruleset(ruleset, ruleset_update, study.version)
        return ruleset.get(scenario_type)
