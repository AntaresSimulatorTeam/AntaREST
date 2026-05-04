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
import contextlib
import io

import numpy as np
import pandas as pd

from antarest.core.serde.np_array import NpArray

# InputSeriesMatrix is the single concrete matrix node class.
# MatrixNode is kept as an alias for backward compatibility.
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
    dump_dataframe,
)

MatrixNode = InputSeriesMatrix

__all__ = ["MatrixNode", "InputSeriesMatrix", "dump_dataframe", "imports_matrix_from_bytes"]


def imports_matrix_from_bytes(data: bytes) -> NpArray | None:
    """Tries to convert bytes to a numpy array when importing a matrix"""
    str_data = data.decode("utf-8")
    if not str_data:
        return np.zeros(shape=(0, 0))
    for delimiter in [",", ";", "\t"]:
        with contextlib.suppress(Exception):
            df = pd.read_csv(io.BytesIO(data), delimiter=delimiter, header=None).replace(",", ".", regex=True)
            df = df.dropna(axis=1, how="all")  # We want to remove columns full of NaN at the import
            matrix = df.to_numpy(dtype=np.float64)
            return matrix
    return None
