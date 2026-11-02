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
from typing import Annotated, TypeAlias

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.model import GemsId
from antarest.core.serde import AntaresBaseModel

Scenario: TypeAlias = Annotated[int, Field(ge=0)]
TimeSerieIndex: TypeAlias = Annotated[int, Field(ge=1)]


class GemsScBuilderMapping(AntaresBaseModel):
    """Associate a zero-based scenario with a one-based data-series column."""

    model_config = ConfigDict(extra="forbid", alias_generator=to_camel)

    scenario: Scenario
    time_series_index: TimeSerieIndex


class GemsScenarioBuilder(AntaresBaseModel):
    """Map each group's zero-based scenarios to one-based data-series columns."""

    model_config = ConfigDict(extra="forbid")

    scenarios: dict[GemsId, list[GemsScBuilderMapping]] = Field(default_factory=dict)


def fill_missing_years(data: list[GemsScBuilderMapping], nb_years: int) -> list[GemsScBuilderMapping]:
    """
    GEMS scenario builder has default values for missing years, we should initialize them for the front-end
    """
    existing = {mapping.scenario for mapping in data}

    return data + [
        GemsScBuilderMapping(scenario=year, time_series_index=year + 1)
        for year in range(nb_years)
        if year not in existing
    ]
