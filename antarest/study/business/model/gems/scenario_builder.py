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

from pydantic import AfterValidator, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel

from antarest.core.model import GemsId
from antarest.core.serde import AntaresBaseModel

Year: TypeAlias = Annotated[int, Field(ge=0)]


class GemsScBuilderMapping(AntaresBaseModel):
    """Associate a zero-based scenario with a one-based data-series column."""

    model_config = ConfigDict(extra="forbid", alias_generator=to_camel, populate_by_name=True)

    scenario: Year
    time_series_index: Year


def _check_scenario_duplication(data: list[GemsScBuilderMapping]) -> list[GemsScBuilderMapping]:
    if len(data) != len(set(mapping.scenario for mapping in data)):
        raise ValueError("Found duplicated scenario inside GEMS scenario builder")
    return data


GemsScBuilderMappings: TypeAlias = Annotated[
    list[GemsScBuilderMapping],
    AfterValidator(_check_scenario_duplication),
    PlainSerializer(lambda x: sorted(x, key=lambda x: x.scenario)),
]


class GemsScenarioBuilder(AntaresBaseModel):
    """Map each group's zero-based scenarios to one-based data-series columns."""

    model_config = ConfigDict(extra="forbid")

    scenarios: dict[GemsId, GemsScBuilderMappings] = Field(default_factory=dict)


def fill_missing_years(data: GemsScBuilderMappings, nb_years: int) -> GemsScBuilderMappings:
    """
    GEMS scenario builder has default values for missing years, we should initialize them for the front-end
    """
    existing = {mapping.scenario for mapping in data}

    new_mapping = data + [
        GemsScBuilderMapping(scenario=year, time_series_index=year) for year in range(nb_years) if year not in existing
    ]
    new_mapping.sort(key=lambda x: x.scenario)
    return new_mapping
