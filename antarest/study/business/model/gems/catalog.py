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

from collections import Counter
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from antarest.core.model import GemsId
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class GemsAggregationOperator(StrEnum):
    SUM = "sum"
    AVG = "avg"


class _GemsCatalogLocation(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    taxonomy_category: str


class _GemsCatalogTerm(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    taxonomy_category: str
    output_id: str
    location_port: str | None = None


class _GemsCatalogBreakdown(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    key: str


class _GemsCatalogFilter(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    key: str
    value: str


class _GemsCatalogMetric(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    terms: list[_GemsCatalogTerm] = Field(default_factory=list)
    terms_operator: GemsAggregationOperator
    time_operator: GemsAggregationOperator
    breakdown: list[_GemsCatalogBreakdown] | None = None
    filter: _GemsCatalogFilter | None = None


class GemsCatalog(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: GemsId
    taxonomy: str
    location: _GemsCatalogLocation
    metrics_definition: list[_GemsCatalogMetric] = Field(default_factory=list)

    @field_validator("metrics_definition")
    @classmethod
    def no_duplicate_metrics(cls, metrics: list[_GemsCatalogMetric]) -> list[_GemsCatalogMetric]:
        duplicates = [metric_id for metric_id, count in Counter(metric.id for metric in metrics).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate metric IDs in catalog: {', '.join(duplicates)}")
        return metrics
