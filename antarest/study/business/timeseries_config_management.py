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

from antarest.study.business.model.config.timeseries_config_model import (
    TimeSeriesConfiguration,
    TimeSeriesConfigurationUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_timeseries_config import UpdateTimeSeriesConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TimeSeriesConfigManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_timeseries_configuration(self, study: StudyInterface) -> TimeSeriesConfiguration:
        """
        Get Time-Series generation values
        """
        return study.get_study_dao().get_timeseries_config()

    def set_timeseries_configuration(
        self, study: StudyInterface, config: TimeSeriesConfigurationUpdate
    ) -> TimeSeriesConfiguration:
        """
        Set Time-Series generation values
        """
        command = UpdateTimeSeriesConfig(
            command_context=self._command_context, study_version=study.version, parameters=config
        )
        study.add_commands([command])
        return self.get_timeseries_configuration(study)
