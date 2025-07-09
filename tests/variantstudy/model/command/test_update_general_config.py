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

from unittest.mock import Mock

import pytest

from antarest.study.business.model.config.general_model import (
    BuildingMode,
    GeneralConfig,
    GeneralConfigUpdate,
    Mode,
    Month,
    WeekDay,
)
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.model.command.update_general_config import UpdateGeneralConfig


@pytest.mark.unit_test
def test_update_general_config_apply_dao(command_context):
    # Mock StudyDao
    mock_study_dao = Mock()

    # Initial GeneralConfig
    initial_config = GeneralConfig(
        horizon="2023",
        nb_years=1,
        mode=Mode.ECONOMY,
        first_day=1,
        last_day=365,
        leap_year=False,
    )
    mock_study_dao.get_general_config.return_value = initial_config

    # Parameters for update
    update_params = GeneralConfigUpdate(
        horizon="2025",
        nb_years=2,
    )

    # Create command instance
    command = UpdateGeneralConfig(
        parameters=update_params,
        study_version=STUDY_VERSION_8_8,
        command_context=command_context,
    )

    # Apply the command
    output = command._apply_dao(mock_study_dao)

    # Assertions
    assert output.status
    assert output.message == "General config updated successfully."

    # Expected updated config
    expected_updated_config = initial_config.model_copy(
        update={
            "horizon": "2025",
            "nb_years": 2,
        }
    )

    mock_study_dao.save_general_config.assert_called_once_with(expected_updated_config)


@pytest.mark.unit_test
def test_update_general_config_apply_dao_more_fields(command_context):
    # Mock StudyDao
    mock_study_dao = Mock()

    # Initial GeneralConfig with more fields
    initial_config = GeneralConfig(
        horizon="2023",
        nb_years=1,
        mode=Mode.ECONOMY,
        first_day=1,
        last_day=365,
        leap_year=False,
        building_mode=BuildingMode.AUTOMATIC,
        first_month=Month.JANUARY,
        first_week_day=WeekDay.MONDAY,
        simulation_synthesis=True,
    )
    mock_study_dao.get_general_config.return_value = initial_config

    # Parameters for update
    update_params = GeneralConfigUpdate(
        horizon="2026",
        nb_years=3,
        building_mode=BuildingMode.CUSTOM,
        first_month=Month.FEBRUARY,
        first_week_day=WeekDay.TUESDAY,
        simulation_synthesis=False,
    )

    # Create command instance
    command = UpdateGeneralConfig(
        parameters=update_params,
        study_version=STUDY_VERSION_8_8,
        command_context=command_context,
    )

    # Apply the command
    output = command._apply_dao(mock_study_dao)

    # Assertions
    assert output.status
    assert output.message == "General config updated successfully."

    # Expected updated config
    expected_updated_config = initial_config.model_copy(
        update={
            "horizon": "2026",
            "nb_years": 3,
            "building_mode": BuildingMode.CUSTOM,
            "first_month": Month.FEBRUARY,
            "first_week_day": WeekDay.TUESDAY,
            "simulation_synthesis": False,
        }
    )

    mock_study_dao.save_general_config.assert_called_once_with(expected_updated_config)


@pytest.mark.unit_test
def test_update_general_config_apply_dao_none_values(command_context):
    # Mock StudyDao
    mock_study_dao = Mock()

    # Initial GeneralConfig
    initial_config = GeneralConfig(
        horizon="2023",
        nb_years=1,
        mode=Mode.ECONOMY,
        first_day=1,
        last_day=365,
        leap_year=False,
        building_mode=BuildingMode.AUTOMATIC,
    )
    mock_study_dao.get_general_config.return_value = initial_config

    # Parameters for update with None values
    update_params = GeneralConfigUpdate(
        horizon=None,
        nb_years=None,
        building_mode=None,
    )

    # Create command instance
    command = UpdateGeneralConfig(
        parameters=update_params,
        study_version=STUDY_VERSION_8_8,
        command_context=command_context,
    )

    # Apply the command
    output = command._apply_dao(mock_study_dao)

    # Assertions
    assert output.status
    assert output.message == "General config updated successfully."

    # Expected updated config should be the same as initial_config
    expected_updated_config = initial_config.model_copy()

    mock_study_dao.save_general_config.assert_called_once_with(expected_updated_config)


def test_update_general_config_to_dto(command_context):
    update_params = GeneralConfigUpdate(
        horizon="2025",
        nb_years=2,
    )
    command = UpdateGeneralConfig(
        parameters=update_params,
        study_version=STUDY_VERSION_8_8,
        command_context=command_context,
    )
    dto = command.to_dto()

    assert dto.action == "update_general_config"
    assert dto.study_version == 880
    assert dto.args == {"parameters": {"horizon": "2025", "nb_years": 2}}
