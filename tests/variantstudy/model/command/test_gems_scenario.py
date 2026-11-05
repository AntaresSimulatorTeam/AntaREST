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
import pytest

from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.model.command.create_gems_scenario import CreateGemsScenario
from antarest.study.storage.variantstudy.model.command.remove_gems_scenario import RemoveGemsScenario
from antarest.study.storage.variantstudy.model.command.update_gems_scenario import UpdateGemsScenario
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_nominal_case(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    dao = dao_10_2
    version = dao.get_version()

    # Create a scenario
    cmd = CreateGemsScenario(
        study_version=version,
        command_context=command_context,
        scenario_name="scenario_1",
        data=[
            GemsScBuilderMapping(scenario=3, time_series_index=1),
            GemsScBuilderMapping(scenario=4, time_series_index=8),
        ],
    )
    result = cmd.apply(dao)
    assert result.status is True

    assert dao.get_gems_scenario_builder() == GemsScenarioBuilder(
        scenarios={
            "scenario_1": [
                GemsScBuilderMapping(scenario=3, time_series_index=1),
                GemsScBuilderMapping(scenario=4, time_series_index=8),
            ]
        }
    )

    # Update the scenario
    cmd2 = UpdateGemsScenario(
        study_version=version,
        command_context=command_context,
        scenario_name="scenario_1",
        data=[
            GemsScBuilderMapping(scenario=0, time_series_index=6),
            GemsScBuilderMapping(scenario=4, time_series_index=7),
        ],
    )
    result = cmd2.apply(dao)
    assert result.status is True

    assert dao.get_gems_scenario_builder() == GemsScenarioBuilder(
        scenarios={
            "scenario_1": [
                GemsScBuilderMapping(scenario=0, time_series_index=6),
                GemsScBuilderMapping(scenario=3, time_series_index=1),  # Unmodified
                GemsScBuilderMapping(scenario=4, time_series_index=7),
            ]
        }
    )

    # Delete the scenario
    cmd3 = RemoveGemsScenario(study_version=version, command_context=command_context, scenario_name="scenario_1")
    result = cmd3.apply(dao)
    assert result.status is True
    assert dao.get_gems_scenario_builder() is None

    ##########################
    # Error cases
    ##########################

    # Ensures we raise when commands are initialized in the wrong version
    error_msg = "GEMS scenario-builder is only available since version 10.2 and was 8.8"
    with pytest.raises(ValueError, match=error_msg):
        CreateGemsScenario(
            study_version=STUDY_VERSION_8_8, command_context=command_context, scenario_name="scenario_1", data=[]
        )

    with pytest.raises(ValueError, match=error_msg):
        UpdateGemsScenario(
            study_version=STUDY_VERSION_8_8, command_context=command_context, scenario_name="scenario_1", data=[]
        )

    with pytest.raises(ValueError, match=error_msg):
        RemoveGemsScenario(study_version=STUDY_VERSION_8_8, command_context=command_context, scenario_name="scenario_1")
