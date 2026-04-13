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
from pydantic import BeforeValidator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel

Variables: TypeAlias = Annotated[list[str], BeforeValidator(lambda x: sorted(x))]


class AreaClusterVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []


ClusterVariables: TypeAlias = Annotated[
    list[AreaClusterVariables], BeforeValidator(lambda x: sorted(x, key=lambda a: a["name"]))
]


class AreaVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []
    thermal_clusters: ClusterVariables = []
    renewable_clusters: ClusterVariables = []
    short_term_storages: ClusterVariables = []


class LinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_1_name: str
    area_2_name: str
    variables: Variables = []


class AreaAndLinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    areas: list[AreaVariables]
    links: list[LinkVariables]


class OutputVariablesList(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mc_ind: AreaAndLinkVariables
    mc_all: AreaAndLinkVariables


class OutputVariablesInformation(AntaresBaseModel, extra="forbid"):
    area: list[str]
    link: list[str]

    @staticmethod
    def from_variables_list(variables_list: OutputVariablesList) -> "OutputVariablesInformation":
        args = {}

        # Areas
        all_area_variables = set()
        for area in variables_list.mc_ind.areas:
            all_area_variables.update(area.variables)
        args["area"] = sorted(all_area_variables)

        # Links
        all_link_variables = set()
        for link in variables_list.mc_ind.links:
            all_link_variables.update(link.variables)
        args["link"] = sorted(all_link_variables)

        return OutputVariablesInformation.model_validate(args)


class OutputVariablesType(StrEnum):
    AREA = "area"
    LINK = "link"
    THERMAL = "thermal"
    RENEWABLE = "renewable"
    SHORT_TERM_STORAGE = "st_storage"


class OutputVariablesViewStatus(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    IN_PROGRESS = "IN_PROGRESS"


class OutputVariablesViewResponse(AntaresBaseModel, extra="forbid", alias_generator=to_camel, populate_by_name=True):
    status: OutputVariablesViewStatus
    task_id: str | None


SingleOutputHeaders: TypeAlias = list[str]
MultipleOutputHeaders: TypeAlias = list[list[str]]


@dataclass(frozen=True)
class VarColumn:
    """
    Column metadata for a variable as defined in output files: variable name, unit name, and statistic (exp, std, ...).
    """

    variable: str
    unit: str
    stat: str | None

    def to_tuple(self) -> tuple[str, str, str]:
        return self.variable, self.unit, (self.stat or "")

    @classmethod
    def from_tuple(cls, tuple_: tuple[str, str, str]) -> "VarColumn":
        return cls(variable=tuple_[0], unit=tuple_[1], stat=tuple_[2])


@dataclass(frozen=True)
class ClusterVarColumn:
    """
    Col metadata for a variable of one cluster:
    in details files, the first line is actually the cluster name, while the second line is considered the variable name
    (ambiguous with unit, actually, for ex. MWh for production).
    Here we keep only that second information.
    """

    variable: str
    stat: str | None


@dataclass(frozen=True)
class OutputDataFrame:
    """
    We separate the polars dataframe and its headers as polars does not handle multi-headers columns.
    """

    data: pl.DataFrame
    headers: list[VarColumn]
