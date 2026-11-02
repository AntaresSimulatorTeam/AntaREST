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


from antarest.study.business.model.gems.scenario_builder import (
    GemsScBuilderMapping,
    GemsScenarioBuilder,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.create_gems_scenario import CreateGemsScenario
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class GemsScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_gems_scenario_builder(self, study: StudyInterface) -> GemsScenarioBuilder:
        return study.get_study_dao().get_gems_scenario_builder() or GemsScenarioBuilder(scenarios={})

    def add_scenario_to_gems_scenario_builder(
        self, study: StudyInterface, scenario_name: str, data: list[GemsScBuilderMapping]
    ) -> list[GemsScBuilderMapping]:
        dao = study.get_study_dao()
        command = CreateGemsScenario(
            scenario_name=scenario_name,
            data=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return dao.get_scenario_from_gems_scenario_builder(scenario_name)

    def delete_scenario_from_gems_scenario_builder(self, study: StudyInterface, scenario_name: str) -> None:
        # todo
        raise NotImplementedError("")
