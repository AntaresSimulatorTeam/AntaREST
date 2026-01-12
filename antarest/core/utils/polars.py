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
import pandas as pd
import polars as pl
from polars.exceptions import ComputeError, NoDataError


def create_polars_dataframe(data: npt.NDArray[np.float64] | list[list[Any]] | pd.DataFrame) -> pl.DataFrame:
    if isinstance(data, list):
        data = np.array(data)
    return pl.DataFrame(data, schema=[str(i) for i in range(data.shape[1])])


def read_input_dataframe(path: Path, has_headers: bool) -> pl.DataFrame:
    try:
        df = pl.read_csv(path, n_threads=1, separator="\t", has_header=has_headers)
    except ComputeError:
        # Happens for file `conversion.txt` as polars infer the data as int64, but the value is too big.
        # In such cases, we'll read the data as a string and convert it in float64 afterward
        df = pl.read_csv(path, n_threads=1, separator="\t", has_header=has_headers, infer_schema=False).with_columns(
            pl.all().cast(pl.Float64)
        )
    except NoDataError:  # if the dataframe is empty
        df = pl.DataFrame()
    return df
