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
from typing import Annotated, Literal, TypeAlias

import polars as pl
from pydantic import BeforeValidator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.core.tables import LazyTable, Table

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


@dataclass(frozen=True)
class VarColumn:
    """
    Column metadata for a variable as defined in output files: variable name, unit name, and statistic (exp, std, ...).

    Statistic is None for mc-ind files, not None for mc-all files.
    """

    variable: str
    unit: str
    stat: str | None

    def to_tuple(self) -> tuple[str, str, str]:
        return self.variable, self.unit, (self.stat or "")


@dataclass(frozen=True)
class ClusterVarColumn:  # TODO: rename to DetailsVarColumn for consistency with data type ?
    """
    Col metadata for a variable of one cluster:
    in details files, the first line is actually the cluster name, while the second line is considered the variable name
    (ambiguous with unit, actually, for ex. MWh for production).
    Here we keep only that second information.
    """

    variable: str
    stat: str | None


# An output column can be any of an "index" column (time step ...), or a full variable column,
# or a "cluster" variable column where unit is not present any more.
OutputColumn: TypeAlias = Literal["area", "link", "cluster", "mcYear", "timeId"] | VarColumn | ClusterVarColumn


def column_to_tuple(col: OutputColumn) -> tuple[str, str, str]:
    match col:
        case VarColumn(var, unit, stat):
            return var, unit, stat or ""
        case ClusterVarColumn(var, stat):
            return var, "", stat or ""
        case _:
            return col, "", ""


# An output table is a polars table with OutputColumn metadata for colums
OutputTable: TypeAlias = Table[pl.DataFrame, OutputColumn]

# Using lazy frames for performance tuning where relevant
LazyOutputTable: TypeAlias = LazyTable[OutputColumn]


class MCIndAreasData(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasData(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksData(StrEnum):
    VALUES = "values"


class MCAllLinksData(StrEnum):
    VALUES = "values"
    ID = "id"


OutputDataType: TypeAlias = MCIndAreasData | MCAllAreasData | MCIndLinksData | MCAllLinksData
