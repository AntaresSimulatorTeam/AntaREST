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
from typing import Annotated, Any, TypeAlias, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from pydantic import BeforeValidator, PlainSerializer


def _list_to_np(array: Any) -> npt.NDArray[np.float64]:
    if isinstance(array, list):
        result = np.array(array, dtype=np.float64)
    elif isinstance(array, np.ndarray):
        result = array
    else:
        raise ValueError("Input should be either a list or a numpy array")
    if result.ndim not in (1, 2):
        raise ValueError(f"Expected 1 or 2 dimensional array, got {result.ndim}")
    return result


def _np_to_list(array: npt.NDArray[np.float64]) -> list[float] | list[list[float]]:
    if array.ndim == 1:
        return cast(list[float], array.tolist())
    elif array.ndim == 2:
        return cast(list[list[float]], array.tolist())
    raise ValueError(f"Expected 1 or 2 dimensional array, got {array.ndim}")


NpArray: TypeAlias = Annotated[npt.NDArray[np.float64], PlainSerializer(_np_to_list), BeforeValidator(_list_to_np)]


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
