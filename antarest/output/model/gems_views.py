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

from pydantic import AliasPath, ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case

# Inputs


class _GemsViewConfigAggregationPattern(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", alias_generator=to_kebab_case)

    id: str
    scenario: bool
    time_granularity: str


class GemsViewConfig(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", alias_generator=to_kebab_case)

    id: str
    taxonomy_category: str = Field(validation_alias=AliasPath("scope", "location", "taxonomy-category"))
    aggregations_patterns: list[_GemsViewConfigAggregationPattern]


# Outputs


class GemsMetricLocation(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    id: str


class GemsAggregationPattern(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    id: str
    scenario: bool
    time_granularity: str


class GemsViewLocations(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    metrics_location: list[GemsMetricLocation]
    aggregation_patterns: list[GemsAggregationPattern]


class GemsTaxonomyViews(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_camel)

    taxonomy: str
    view_ids: list[dict[str, GemsViewLocations]]
