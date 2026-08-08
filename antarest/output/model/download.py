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
"""
Models for the deprecated "download output" feature.
"""

from enum import StrEnum
from typing import Annotated, TypeAlias

import pandas as pd
from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.model import MatrixFrequency


class StudyDownloadType(StrEnum):
    LINK = "LINK"
    DISTRICT = "DISTRICT"
    AREA = "AREA"


class StudyDownloadDTO(AntaresBaseModel, alias_generator=to_camel):
    """
    DTO used to download outputs
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


class MatrixIndex(AntaresBaseModel):
    start_date: str = ""
    steps: int = 8760
    first_week_size: int = 7
    level: MatrixFrequency = MatrixFrequency.HOURLY

    def set_as_df_index(self, df: pd.DataFrame) -> None:
        time_column = pd.date_range(start=self.start_date, periods=len(df), freq=self.level.value[0])
        df.index = time_column


class TimeSerie(AntaresBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, ser_json_inf_nan="constants")

    name: str
    unit: str
    data: list[float | None]


VariableName: TypeAlias = str


class TimeSeriesData(AntaresBaseModel):
    """
    Data for one element of the system (area or link).
    """

    type: StudyDownloadType
    name: str
    data: dict[VariableName, list[TimeSerie]] = {}


class MatrixAggregationResultDTO(AntaresBaseModel):
    index: MatrixIndex
    data: list[TimeSeriesData]
