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
from pathlib import Path
from typing import Iterator, TypeAlias

import pandas as pd
import polars as pl
from polars.exceptions import ComputeError

from antarest.study.model import MatrixFrequency, MatrixIndex, TimeSerie

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


@dataclass
class OutputDataFrame:
    data: pl.DataFrame
    headers: list[list[str]] | list[str]


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


def concatenate_dataframe_multi_indexed_columns(data: OutputDataFrame) -> None:
    """
    Used inside Imagrid endpoint as we want to keep the unit of the column but pyarrow doesn't handle MultiIndex.
    """
    data.headers = [" % ".join(col) for col in data.headers]


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


def _parse_output_dataframe(file_path: Path) -> pl.DataFrame:
    try:
        return pl.read_csv(file_path, skip_lines=7, separator="\t", has_header=False, null_values="N/A", n_threads=1)
    except ComputeError:
        # Happens if polars wrongly inferred the schema.
        # If so, we specify that it should read the entire file to be sure it doesn't infer a false schema.
        # It's significantly slower but it does not fail.
        # As no file is longer than 10.000 rows we use this value.
        return pl.read_csv(
            file_path,
            skip_lines=7,
            separator="\t",
            has_header=False,
            null_values="N/A",
            infer_schema_length=10000,
            n_threads=1,
        )


def parse_output_file(file_path: Path, first_column: int) -> OutputDataFrame:
    content = file_path.read_text(encoding="utf-8")
    output_headers = parse_headers(content, first_column)
    polars_df = _parse_output_dataframe(file_path)

    df = polars_df[polars_df.columns[first_column:]]

    # At this point we only have numeric values in our df. But NaN columns are considered to be String by polars.
    # So we change this to be Float64 to harmonize everything.
    df = df.with_columns(pl.col(pl.Utf8).cast(pl.Float64))

    return OutputDataFrame(data=df, headers=output_headers)
