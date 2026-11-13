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

from pydantic import AliasPath, ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class GemsTimeGranularity(StrEnum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class _GemsViewConfigAggregationPattern(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", alias_generator=to_kebab_case)

    id: str
    scenario: bool
    time_granularity: GemsTimeGranularity


class GemsViewConfig(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", alias_generator=to_kebab_case)

    id: str
    taxonomy_category: str = Field(validation_alias=AliasPath("scope", "location", "taxonomy-category"))
    aggregations_patterns: list[_GemsViewConfigAggregationPattern]
