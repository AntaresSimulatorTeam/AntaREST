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
from typing import cast

import numpy as np
import pandas as pd
import polars as pl
from polars.exceptions import ComputeError, NoDataError

from antarest.core.config import InternalMatrixFormat
from antarest.core.serde.matrix_export import write_dataframe_in_tsv_format


def load_matrix(matrix_format: InternalMatrixFormat, path: Path, matrix_version: int) -> pl.DataFrame:
    if matrix_format == InternalMatrixFormat.TSV:
        # Based on the matrix version, we assume its format
        if matrix_version == 1:
            df = pl.DataFrame(data=np.loadtxt(path, delimiter="\t", dtype=np.float64, ndmin=2))
        else:
            try:
                df = pl.read_csv(path, n_threads=1, separator="\t", has_header=True)
            except ComputeError:
                # Happens for file `conversion.txt` as polars infer the data as int64, but the value is too big.
                # In such cases, we'll read the data as a string and convert it in float64 afterward
                df = pl.read_csv(path, n_threads=1, separator="\t", has_header=True, infer_schema=False).with_columns(
                    pl.all().cast(pl.Float64)
                )
            except NoDataError:  # if the dataframe is empty
                df = pl.DataFrame()
    elif matrix_format == InternalMatrixFormat.HDF:
        pandas_df = cast(pd.DataFrame, pd.read_hdf(path))
        df = pl.from_pandas(pandas_df)
    elif matrix_format == InternalMatrixFormat.PARQUET:
        df = pl.read_parquet(path)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        df = pl.read_ipc(path, memory_map=False)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")

    # Specific treatment to change default polars columns
    length_range = range(len(df.columns))
    if df.columns == [f"column_{k}" for k in length_range]:
        df.columns = [str(k) for k in length_range]
    return df


def save_matrix(matrix_format: InternalMatrixFormat, dataframe: pl.DataFrame, path: Path) -> None:
    if matrix_format == InternalMatrixFormat.TSV:
        write_dataframe_in_tsv_format(dataframe, path, headers=True)
    elif matrix_format == InternalMatrixFormat.HDF:
        dataframe.to_pandas().to_hdf(str(path), key="data", index=False)
    elif matrix_format == InternalMatrixFormat.PARQUET:
        dataframe.write_parquet(path)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        dataframe.write_ipc(path)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")
