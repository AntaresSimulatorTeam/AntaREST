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

from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.model.command.create_gems_scenario import CreateGemsScenario
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

    dao.save_general_config(GeneralConfig(nb_years=4))  # Default values are based on this number

    assert dao.get_gems_scenario_builder() == GemsScenarioBuilder(
        scenarios={
            "scenario_1": [
                GemsScBuilderMapping(scenario=0, time_series_index=1),
                GemsScBuilderMapping(scenario=1, time_series_index=2),
                GemsScBuilderMapping(scenario=2, time_series_index=3),
                GemsScBuilderMapping(scenario=3, time_series_index=1),
                GemsScBuilderMapping(scenario=4, time_series_index=8),
            ]
        }
    )

    # Ensures we raise when command in initialized in the wrong version
    with pytest.raises(ValueError, match="GEMS scenario-builder is only available since version 10.2 and was 8.8"):
        CreateGemsScenario(
            study_version=STUDY_VERSION_8_8, command_context=command_context, scenario_name="scenario_1", data=[]
        )
