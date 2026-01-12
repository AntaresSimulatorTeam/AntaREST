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
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import polars as pl


def create_polars_dataframe(data: npt.NDArray[np.float64] | list[list[Any]] | pd.DataFrame) -> pl.DataFrame:
    if isinstance(data, list):
        data = np.array(data)
    return pl.DataFrame(data, schema=[str(i) for i in range(data.shape[1])])
