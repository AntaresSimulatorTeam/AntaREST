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

from antarest.core.serde import AntaresBaseModel


class TimeSeriesType(AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True):
    number: int = 1


class TimeSeriesConfiguration(AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True):
    thermal: TimeSeriesType = TimeSeriesType()


class TimeSeriesConfigurationUpdate(AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True):
    thermal: TimeSeriesType | None = None


def update_timeseries_configuration(
    config: TimeSeriesConfiguration, data: TimeSeriesConfigurationUpdate
) -> TimeSeriesConfiguration:
    """
    Updates the timeseries configuration according to the provided update data.
    """
    current_config = config.model_dump(mode="json")
    new_config = data.model_dump(mode="json", exclude_none=True)
    current_config.update(new_config)
    return TimeSeriesConfiguration.model_validate(current_config)
