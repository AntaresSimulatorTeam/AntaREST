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

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel


class GemsScBuilderMapping(AntaresBaseModel):
    """Associate a zero-based scenario with a one-based data-series column."""

    model_config = ConfigDict(extra="forbid")

    scenario: int = Field(ge=0)
    time_series_index: int = Field(ge=1)


class GemsScenarioBuilder(AntaresBaseModel):
    """Map each group's zero-based scenarios to one-based data-series columns."""

    model_config = ConfigDict(extra="forbid")

    scenarios: dict[str, list[GemsScBuilderMapping]] = Field(default_factory=dict)
