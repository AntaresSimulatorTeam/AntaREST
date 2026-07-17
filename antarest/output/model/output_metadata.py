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
from typing import Any

from pydantic import ConfigDict, Field, model_serializer
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import SerializerFunctionWrapHandler

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.config.general_model import Mode


class OutputStorageType(StrEnum):
    IN_STUDY_FILE_TREE = "IN_STUDY_FILE_TREE"
    V2 = "V2"
    OUT_OF_STUDY_FILE_TREE = "OUT_OF_STUDY_FILE_TREE"


@dataclass(frozen=True)
class OutputMetadata:
    """
    Simplest metadata for a study output.

    Attributes:
        id:       unique identifier of the output
        in_study: whether the output is stored in the study file tree. Here the abstraction is clearly leaky,
                  but we need it for compatibility with existing file studies, at archival time, to decide if
                  the study should be archived separately or not.
    """

    id: str
    in_study: bool
    archived: bool


# The following settings class are used by a known client,
# we keep it here for compatibility reasons, but that could be removed in the future


class OutputSettingsGeneral(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    mode: str
    horizon: str
    nbyears: int
    simulation_start: int = Field(alias="simulation.start")
    simulation_end: int = Field(alias="simulation.end")
    january_1st: str = Field(alias="january.1st")
    first_month_in_year: str = Field(alias="first-month-in-year")
    first_weekday: str = Field(alias="first.weekday")
    leapyear: bool
    year_by_year: bool = Field(alias="year-by-year")
    user_playlist: bool = Field(alias="user-playlist")


class OutputSettingsOptimization(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )
    transmission_capacities: str | bool = Field(alias="transmission-capacities")


class OutputSettings(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    general: OutputSettingsGeneral
    optimization: OutputSettingsOptimization
    playlist: list[int] | None = None


class OutputDetails(AntaresBaseModel):
    """
    More detailed metadata about a study output.
    """

    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )

    id: str
    name: str
    mode: Mode
    synthesis: bool
    by_year: bool
    nb_years: int
    archived: bool
    storage_type: OutputStorageType

    settings: OutputSettings | None = Field(deprecated=True, default=None)

    @model_serializer(mode="wrap")
    def _serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data: dict[str, object] = handler(self)
        if data.get("settings") is None:
            data.pop("settings", None)
        return data
