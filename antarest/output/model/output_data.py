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
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, TypeAlias

import polars as pl
from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.model import MatrixFrequency


@dataclass(frozen=True)
class VariableDescription:
    name: str
    unit: str
    stat: str | None


@dataclass(frozen=True)
class OutputTable:
    columns: list[VariableDescription]
    data: pl.DataFrame


AreaOutputData: TypeAlias = OutputTable
LinkOutputData: TypeAlias = OutputTable

################################################################################
# The models below are related to the deprecated feature "download_output".
################################################################################


class MatrixIndex(AntaresBaseModel):
    start_date: str = ""
    steps: int = 8760
    first_week_size: int = 7
    level: MatrixFrequency = MatrixFrequency.HOURLY


class StudyDownloadType(StrEnum):
    LINK = "LINK"
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class StudyDownloadDTO(AntaresBaseModel, alias_generator=to_camel, populate_by_name=True):
    """
    Describes the output data the user has requested
    """

    type: StudyDownloadType
    years: list[int] = []
    level: MatrixFrequency
    filter_in: Annotated[str | None, Field(deprecated=True, default=None)]  # We don't consider it
    filter_out: Annotated[str | None, Field(deprecated=True, default=None)]  # We don't consider it
    filter: list[str] = []
    columns: list[str] = []
    synthesis: Annotated[bool, Field(deprecated=True, default=False)]  # We always consider it's False
    include_clusters: bool = False

    @model_validator(mode="after")
    def check_coherence(self) -> "StudyDownloadDTO":
        if self.include_clusters and self.type == StudyDownloadType.LINK:
            raise ValueError("Cannot ask for cluster values for type link")
        return self


class TimeSerie(AntaresBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, ser_json_inf_nan="constants")

    name: str
    unit: str
    data: list[float | None]


class TimeSeriesData(AntaresBaseModel):
    type: StudyDownloadType
    name: str
    data: dict[str, list[TimeSerie]] = {}


class MatrixAggregationResultDTO(AntaresBaseModel):
    data: list[TimeSeriesData]
    index: MatrixIndex
