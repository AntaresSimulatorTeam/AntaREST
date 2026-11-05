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
from antarest.core.exceptions import GemsScenarioAlreadyExists
from antarest.core.model import GemsId
from antarest.study.business.model.gems.scenario_builder import (
    GemsScBuilderMappings,
    GemsScenarioBuilder,
    fill_missing_years,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao
from antarest.study.storage.variantstudy.model.command.create_gems_scenario import CreateGemsScenario
from antarest.study.storage.variantstudy.model.command.remove_gems_scenario import RemoveGemsScenario
from antarest.study.storage.variantstudy.model.command.update_gems_scenario import UpdateGemsScenario
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _get_sc_builder_mappings_filled(dao: ReadOnlyStudyDao, scenario_name: GemsId) -> GemsScBuilderMappings:
    sc_builder_mappings = dao.get_scenario_from_gems_scenario_builder(scenario_name)
    simulation_nb_years = dao.get_general_config().nb_years
    return fill_missing_years(sc_builder_mappings, simulation_nb_years)


class GemsScenarioBuilderManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_gems_scenario_builder(self, study: StudyInterface) -> GemsScenarioBuilder:
        dao = study.get_study_dao()
        sc_builder = dao.get_gems_scenario_builder()
        if not sc_builder:
            return GemsScenarioBuilder(scenarios={})

        simulation_nb_years = dao.get_general_config().nb_years
        for scenario_id, mappings in sc_builder.scenarios.items():
            sc_builder.scenarios[scenario_id] = fill_missing_years(mappings, simulation_nb_years)

        return sc_builder

    def add_scenario_to_gems_scenario_builder(
        self, study: StudyInterface, scenario_name: GemsId, data: GemsScBuilderMappings
    ) -> GemsScBuilderMappings:
        dao = study.get_study_dao()
        # First ensures the scenario does not already exist
        if dao.scenario_exists_in_gems_scenario_builder(scenario_name):
            raise GemsScenarioAlreadyExists(scenario_name, study.id)

        command = CreateGemsScenario(
            scenario_name=scenario_name,
            data=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return _get_sc_builder_mappings_filled(dao, scenario_name)

    def update_scenario_from_gems_scenario_builder(
        self, study: StudyInterface, scenario_name: GemsId, data: GemsScBuilderMappings
    ) -> GemsScBuilderMappings:
        dao = study.get_study_dao()
        # First ensures the scenario exists
        dao.get_scenario_from_gems_scenario_builder(scenario_name)

        command = UpdateGemsScenario(
            scenario_name=scenario_name,
            data=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return _get_sc_builder_mappings_filled(dao, scenario_name)

    def delete_scenario_from_gems_scenario_builder(self, study: StudyInterface, scenario_name: GemsId) -> None:
        # First ensures the scenario exists
        study.get_study_dao().get_scenario_from_gems_scenario_builder(scenario_name)

        command = RemoveGemsScenario(
            scenario_name=scenario_name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
