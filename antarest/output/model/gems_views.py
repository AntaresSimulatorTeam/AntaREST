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

from enum import StrEnum
from typing import TypeAlias

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.gems.view import GemsTimeGranularity

ViewId: TypeAlias = str


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


class OutputGemsViewsStatus(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    IN_PROGRESS = "IN_PROGRESS"


class OutputGemsViewsResponse(AntaresBaseModel, extra="forbid", alias_generator=to_camel, populate_by_name=True):
    status: OutputGemsViewsStatus
    task_id: str | None
