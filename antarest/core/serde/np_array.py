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
from typing import Annotated, TypeAlias, cast

import numpy as np
import numpy.typing as npt
from pydantic import BeforeValidator, PlainSerializer


def _list_to_np(array: list[float]) -> npt.NDArray[np.float64]:
    return np.array(array, dtype=np.float64)


def _np_to_list(array: npt.NDArray[np.float64]) -> list[float]:
    return cast(list[float], array.tolist())


NpArray: TypeAlias = Annotated[npt.NDArray[np.float64], PlainSerializer(_np_to_list), BeforeValidator(_list_to_np)]
