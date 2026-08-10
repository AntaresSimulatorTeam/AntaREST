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
Utilities for parsing output matrix files (text files).
"""

from io import StringIO
from itertools import islice
from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd
import polars as pl
from polars._plr import ComputeError

from antarest.output.filestudy.model import OutputDataFrame, VariableDescription
from antarest.study.model import MatrixFrequency


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


def parse_headers(content: IO[str], start_col: int) -> list[VariableDescription]:
    header_lines: list[list[str]] = []
    for line in islice(content, 4, 7):  # Note: avoids to go over the whole file, much faster for larger files
        cols = line.rstrip("\n").split("\t")[start_col:]
        if not header_lines:
            header_lines = [[col] for col in cols]
        else:
            for k, col in enumerate(cols):
                header_lines[k].append(col)

    def none_if_empty(value: str) -> str | None:
        return None if not value.strip() else value

    return [
        VariableDescription(name=col[0], unit=none_if_empty(col[1]), statistic_type=none_if_empty(col[2]))
        for col in header_lines
    ]


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


def parse_output_file(file_path: Path, first_column: int) -> OutputDataFrame[VariableDescription]:
    content = file_path.read_text(encoding="utf-8")
    output_headers = parse_headers(StringIO(content), first_column)
    polars_df = _parse_output_dataframe(file_path)

    df = polars_df[polars_df.columns[first_column:]]

    # At this point we only have numeric values in our df. But NaN columns are considered to be String by polars.
    # So we change this to be Float64 to harmonize everything.
    df = df.with_columns(pl.col(pl.Utf8).cast(pl.Float64))

    return OutputDataFrame(data=df, headers=output_headers)


def parse_output_file_as_pandas_dataframe(file_path: Path, first_column: int) -> pd.DataFrame:
    output = parse_output_file(file_path, first_column)
    df = output.data.to_pandas().astype(np.float64)
    df.columns = pd.MultiIndex.from_tuples(output.headers)  # type: ignore
    return df
