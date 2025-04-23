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
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from antarest.core.config import InternalMatrixFormat


def load_matrix(matrix_format: InternalMatrixFormat, path: Path, matrix_version: int) -> pd.DataFrame:
    if matrix_format == InternalMatrixFormat.TSV:
        # Based on the matrix version, we assume its format
        if matrix_version == 1:
            df = pd.DataFrame(data=np.loadtxt(path, delimiter="\t", dtype=np.float64, ndmin=2))
        else:
            try:
                df = pd.read_csv(path, sep="\t", header=0)
            except pd.errors.EmptyDataError:  # Pandas cannot read an empty DataFrame
                df = pd.DataFrame()
    elif matrix_format == InternalMatrixFormat.HDF:
        df = cast(pd.DataFrame, pd.read_hdf(path))
    elif matrix_format == InternalMatrixFormat.PARQUET:
        df = pd.read_parquet(path)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        df = pd.read_feather(path)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")

    # Specific treatment on columns for each format to have the same behavior
    length_range = range(len(df.columns))
    if list(df.columns) == [str(k) for k in length_range]:
        df.columns = pd.Index(length_range)  # type: ignore
    return df


def save_matrix(matrix_format: InternalMatrixFormat, dataframe: pd.DataFrame, path: Path) -> None:
    if matrix_format == InternalMatrixFormat.TSV:
        dataframe.to_csv(path, sep="\t", float_format="%.6f", index=False)
    elif matrix_format == InternalMatrixFormat.HDF:
        dataframe.to_hdf(str(path), key="data", index=False)
    elif matrix_format == InternalMatrixFormat.PARQUET:
        dataframe.to_parquet(path, compression=None, index=False)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        dataframe.to_feather(path)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")
