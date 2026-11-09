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
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import polars as pl
from polars import DataFrame
from polars.exceptions import ComputeError, NoDataError


def create_polars_dataframe(data: npt.NDArray[np.float64] | list[list[Any]]) -> pl.DataFrame:
    if isinstance(data, list):
        data = np.array(data)
    polars_df = pl.DataFrame(data)
    # We have to rename the columns as polars uses `column_0`, `column_1`, ... by default.
    # But we cannot give him a schema at creation as it can transpose the data for some obscure reason in that case.
    return polars_df.rename({col: str(k) for k, col in enumerate(polars_df.columns)})


def read_tsv(path: Path, has_headers: bool) -> pl.DataFrame:
    return _read_file(path, has_headers, separator="\t")


def _read_file(path: Path, has_headers: bool, separator: str) -> pl.DataFrame:
    try:
        df = pl.read_csv(path, n_threads=1, separator=separator, has_header=has_headers)
    except ComputeError:
        # Happens for file `conversion.txt` as polars infer the data as int64, but the value is too big.
        # In such cases, we'll read the data as a string and convert it in float64 afterward
        df = _read_file_with_floats(has_headers, path, separator)
    except NoDataError:  # if the dataframe is empty
        df = pl.DataFrame()
    return df


def _read_file_with_floats(has_headers: bool, path: Path, separator: str) -> DataFrame:
    df = pl.read_csv(path, n_threads=1, separator=separator, has_header=has_headers, infer_schema=False).with_columns(
        pl.all().str.strip_chars().cast(pl.Float64)
    )
    return df


def write_csv(data: pl.DataFrame, path: Path) -> None:
    data.write_csv(path, include_header=False, separator=",")
