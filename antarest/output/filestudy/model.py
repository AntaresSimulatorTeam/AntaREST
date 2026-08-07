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
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Literal, TypeAlias

import pandas as pd
import polars as pl

from antarest.output.model.download import TimeSerie

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


SingleOutputHeaders: TypeAlias = list[str]
MultipleOutputHeaders: TypeAlias = list[list[str]]


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


@dataclass
class OutputDataFrame:
    """
    We separate the polars dataframe and its headers as polars does not handle multi-headers columns.
    """

    data: pl.DataFrame
    headers: SingleOutputHeaders | MultipleOutputHeaders


def normalize_df_column_names(mc_root: MCRoot, output_headers: list[list[str]]) -> list[str]:
    """
    That "normal form" is :
     - for mc-ind, only the variable name "Var"
     - for mc-all, the concatenation of variable name and stat type in upper case ... "VAR EXP"
    """
    if mc_root == MCRoot.MC_IND:
        return [col[0] for col in output_headers]
    return [" ".join([col[0], col[2]]).upper().strip() for col in output_headers]


def concatenate_dataframe_multi_indexed_columns(data: OutputDataFrame) -> None:
    """
    Serializes multi-indexed column headers into a single string, concatenating with " % " as a separator.
    """
    data.headers = [" % ".join(col) for col in data.headers]


def split_concatenated_columns_from_dataframe(df: pd.DataFrame) -> Iterator[TimeSerie]:
    """
    Performs the inverse transformation compared to the concatenate method. Also used inside Imagrid endpoint.
    """
    for column in df.columns:
        splitted_col = column.split(" % ")
        name, unit = splitted_col[0], splitted_col[1]
        yield TimeSerie(name=name, unit=unit or " ", data=df[column].to_list())
