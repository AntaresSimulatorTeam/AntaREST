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
from typing import Annotated, Any, TypeAlias

import numpy as np
import numpy.typing as npt
from pydantic import BeforeValidator, PlainSerializer


def _list_to_np(array: Any) -> npt.NDArray[np.float64]:
    if isinstance(array, list):
        return np.array(array, dtype=np.float64)
    elif isinstance(array, np.ndarray):
        return array
    raise ValueError("Input should be either a list or a numpy array")


def _np_to_list(array: npt.NDArray[np.float64]) -> list[float] | list[list[float]]:
    if array.ndim == 1:
        return [float(x) for x in array]
    elif array.ndim == 2:
        return [[float(x) for x in row] for row in array]
    raise ValueError(f"Expected 1 or 2 dimensional array, got {array.ndim}")


NpArray: TypeAlias = Annotated[npt.NDArray[np.float64], PlainSerializer(_np_to_list), BeforeValidator(_list_to_np)]
