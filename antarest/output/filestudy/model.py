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
from enum import Enum, StrEnum
from typing import Callable, Generic, Literal, Sequence, TypeAlias, TypeVar

import polars as pl

"""Column name for the Monte Carlo year."""
MCYEAR_COL = "mcYear"

"""Column name for the time index."""
TIME_ID_COL = "timeId"


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


class MCIndAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksQueryFile(StrEnum):
    VALUES = "values"


class MCAllLinksQueryFile(StrEnum):
    VALUES = "values"
    ID = "id"


QueryFileType: TypeAlias = MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile

AggregationType: TypeAlias = Literal["mc-all", "mc-ind"]


def aggregation_type(file_type: QueryFileType) -> AggregationType:
    match file_type:
        case MCIndAreasQueryFile() | MCIndLinksQueryFile():
            return "mc-ind"
        case MCAllAreasQueryFile() | MCAllLinksQueryFile():
            return "mc-all"
        case _:
            raise ValueError(f"Unknown output file type: {file_type}")


@dataclass(frozen=True, slots=True)
class VariableDescription:
    """
    Represents the metadata of an output file column.

    Could probably be refined, see descriptions below, to better represent the actual usage (mc-all/mc-ind, details/values ...)

    Attributes:
        name: the name of the variable. Sometimes, used for an element name such as a cluster name (for example in
              "details" files).
        unit: unit of the variable. In output files ("details" files), this is actually sometimes used as a substitute
              for the name (NP COST - Euro for example), because the variable name is actually used for the cluster name.
        statistic_type: for mc-all outputs, this defines what statistic this represents: expectations, standard dev,
                        min, max ...
    """

    name: str
    unit: str | None
    statistic_type: str | None

    def to_tuple(self) -> tuple[str, str, str]:
        # Follows convention of output files ... maybe better keep it instead of None after all ?
        return self.name, self.unit_repr(), self.statistic_type_repr()

    def unit_repr(self) -> str:
        """
        Representation of the unit as in output files, never None.
        """
        return self.unit or " "

    def statistic_type_repr(self) -> str:
        """
        Representation of the statistic type as in output files, never None.
        """
        return self.statistic_type or ""

    def normal_repr(self) -> str:
        """
        That "normal form" is :
         - for mc-ind, only the variable name "Var"
         - for mc-all, the concatenation of variable name and stat type in upper case ... "VAR EXP"

        Cannot see any justification for that convention, it's inherited implicit choices from the past,
        could be changed in the future.
        """
        mc_ind = self.statistic_type is None
        if mc_ind:
            return self.name
        return f"{self.name} {self.statistic_type_repr()}".upper().strip()


def get_output_object_type(
    file_type: QueryFileType, is_link: bool
) -> Literal["areas", "links", "thermal_clusters", "renewable_clusters", "short_term_storages"]:
    if is_link:
        return "links"

    match file_type:
        case MCIndAreasQueryFile.DETAILS:
            return "thermal_clusters"
        case MCIndAreasQueryFile.DETAILS_RES:
            return "renewable_clusters"
        case MCIndAreasQueryFile.DETAILS_ST_STORAGE:
            return "short_term_storages"
        case _:
            return "areas"


C = TypeVar("C")
C2 = TypeVar("C2")


@dataclass
class OutputDataFrame(Generic[C]):
    """
    We separate the polars dataframe and its headers as polars does not handle multi-headers columns.

    Attributes:
        C: Type holding columns metadata
    """

    data: pl.DataFrame
    headers: list[C]

    def __init__(self, data: pl.DataFrame, headers: Sequence[C]):
        self.data = data
        self.headers = list(headers)

    def __post_init__(self) -> None:
        if len(self.headers) != len(self.data.columns):
            raise ValueError("The number of headers must match the number of columns in the dataframe")

    def map_metadata(self, func: Callable[[C], C2]) -> "OutputDataFrame[C2]":
        return OutputDataFrame(self.data, [func(col) for col in self.headers])
