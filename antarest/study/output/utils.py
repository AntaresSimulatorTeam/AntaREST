# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from enum import Enum, StrEnum
from typing import Iterator, TypeAlias

import pandas as pd

from antarest.study.model import MatrixFrequency, MatrixIndex, TimeSerie

"""Column name for the Monte Carlo year."""
MCYEAR_COL = "mcYear"


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


def normalize_df_column_names(mc_root: MCRoot, output_headers: list[list[str]]) -> list[str]:
    if mc_root == MCRoot.MC_IND:
        return [col[0] for col in output_headers]
    return [" ".join([col[0], col[2]]).upper().strip() for col in output_headers]


def get_start_column(frequency: MatrixFrequency) -> int:
    if frequency == MatrixFrequency.ANNUAL:
        return 2
    elif frequency == MatrixFrequency.MONTHLY:
        return 3
    elif frequency == MatrixFrequency.WEEKLY:
        return 2
    elif frequency == MatrixFrequency.DAILY:
        return 4
    elif frequency == MatrixFrequency.HOURLY:
        return 5
    else:
        raise NotImplementedError(f"Unknown frequency {frequency.value}")


def parse_headers(content: str, start_col: int) -> list[list[str]]:
    lines = content.splitlines()
    header_lines = []
    for idx, line in enumerate(lines[4:7]):
        cols = line.split("\t")[start_col:]
        if idx == 0:
            header_lines = [[col] for col in cols]
        else:
            for k, col in enumerate(cols):
                header_lines[k].append(col)

    return header_lines


def concatenate_dataframe_multi_indexed_columns(df: pd.DataFrame) -> None:
    """
    Used inside Imagrid endpoint as we want to keep the unit of the column but pyarrow doesn't handle MultiIndex.
    """
    df.columns = pd.Index([" % ".join(col) for col in df.columns])


def split_concatenated_columns_from_dataframe(df: pd.DataFrame) -> Iterator[TimeSerie]:
    """
    Performs the inverse transformation compared to the concatenate method. Also used inside Imagrid endpoint.
    """
    for column in df.columns:
        splitted_col = column.split(" % ")
        name, unit = splitted_col[0], splitted_col[1]
        yield TimeSerie(name=name, unit=unit or " ", data=df[column].to_numpy())


def add_time_index_to_dataframe(df: pd.DataFrame, matrix_index: MatrixIndex) -> None:
    time_column = pd.date_range(start=matrix_index.start_date, periods=len(df), freq=matrix_index.level.value[0])
    df.index = time_column
