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

from datetime import datetime
from typing import TypeAlias

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.gems.view import GemsTimeGranularity

ViewId: TypeAlias = str
# `(variable, unit, stat)`
GemsViewColumn: TypeAlias = tuple[str, str, str]


class GemsMetricLocation(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    id: str


class GemsAggregationPattern(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    id: str
    scenario: bool
    time_granularity: GemsTimeGranularity


class GemsViewLocations(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    metrics_location: list[GemsMetricLocation]
    aggregation_patterns: list[GemsAggregationPattern]


class GemsTaxonomyViews(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    taxonomy: str
    view_ids: dict[ViewId, GemsViewLocations]


class GemsViewIndex(AntaresBaseModel):
    """
    Dates of the rows of a view matrix: row `i` is `start_date` plus `i * step_size` periods.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, alias_generator=to_camel)

    start_date: datetime | None = Field(description="Date of the first row, null if undated or empty.")
    steps: int
    time_granularity: GemsTimeGranularity
    step_size: int = Field(
        description="Number of periods of the time granularity between two rows.",
    )


class GemsViewMatrix(AntaresBaseModel):
    """
    One location of a view as a matrix, shaped like the output matrices of `GET /raw`, plus the row index.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: GemsViewIndex
    columns: list[GemsViewColumn] = Field(description="`[variable, unit, stat]` triples")
    data: list[list[float | None]] = Field(description="One row per step, one value per column")
