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

import pandas as pd

from antarest.core.config import InternalMatrixFormat


def load_matrix(matrix_format: InternalMatrixFormat, path: Path) -> pd.DataFrame:
    if path.stat().st_size == 0:
        return pd.DataFrame()
    if matrix_format == InternalMatrixFormat.TSV:
        # The legacy format is TSV, so we have to handle both cases
        # To know if we're opening a legacy matrix or not we have to seek the first bytes of the file
        # Legacy
        header = None
        index_col = None
        with open(path, "r") as f:
            if f.read(1) == "\t":
                # New format
                header = 0
                index_col = 0
        df = pd.read_csv(path, sep="\t", index_col=index_col, header=header)
        # Specific treatment on columns to fit with other formats
        length_range = range(len(df.columns))
        if list(df.columns) == [str(k) for k in length_range]:
            df.columns = pd.Index(length_range)  # type: ignore
        return df
    elif matrix_format == InternalMatrixFormat.HDF:
        return cast(pd.DataFrame, pd.read_hdf(path))
    elif matrix_format == InternalMatrixFormat.PARQUET:
        return pd.read_parquet(path)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        return pd.read_feather(path)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")


def save_matrix(matrix_format: InternalMatrixFormat, dataframe: pd.DataFrame, path: Path) -> None:
    if matrix_format == InternalMatrixFormat.TSV:
        dataframe.to_csv(path, sep="\t", float_format="%.6f")
    elif matrix_format == InternalMatrixFormat.HDF:
        dataframe.to_hdf(str(path), key="data")
    elif matrix_format == InternalMatrixFormat.PARQUET:
        dataframe.to_parquet(path, compression=None)
    elif matrix_format == InternalMatrixFormat.FEATHER:
        dataframe.to_feather(path)
    else:
        raise NotImplementedError(f"Internal matrix format '{matrix_format}' is not implemented")
