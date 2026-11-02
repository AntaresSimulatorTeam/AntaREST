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
    fill_missing_years,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class GemsScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_gems_scenario_builder(self, study: StudyInterface) -> GemsScenarioBuilder:
        return study.get_study_dao().get_gems_scenario_builder() or GemsScenarioBuilder(scenarios={})

    def add_scenario_to_gems_scenario_builder(
        self, study: StudyInterface, scenario_name: str, data: list[GemsScBuilderMapping]
    ) -> list[GemsScBuilderMapping]:
        simulation_nb_years = study.get_study_dao().get_general_config().nb_years
        filled_scenario = fill_missing_years(data, simulation_nb_years)
        return filled_scenario

    def delete_scenario_from_gems_scenario_builder(self, study: StudyInterface, scenario_name: str) -> None:
        # todo
        raise NotImplementedError("")
