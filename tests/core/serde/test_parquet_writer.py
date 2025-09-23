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
from typing import Iterator

import numpy as np
import pandas as pd
import pytest

from antarest.core.serde.parquet_writer import (
    write_dataframes_in_parquet_format_by_column_sets,
    yield_parquet_dataframes,
)


@pytest.fixture
def dataframes() -> Iterator[pd.DataFrame]:
    return iter(
        [
            pd.DataFrame(data=[(10, 11), (12, 13)], columns=["A", "B"]),
            pd.DataFrame(data=[(12, 13), (14, 15)], columns=["C", "B"]),
        ]
    )


def test_different_columns(tmp_path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
    all_df_names, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert all_df_names == ["file0.parquet", "file1.parquet"]
    assert all_cols == ["A", "B", "C"]

    dfs = yield_parquet_dataframes(tmp_path, all_df_names, all_cols)

    expected_first_df = pd.DataFrame(data=[(10, 11, np.NaN), (12, 13, np.NaN)], columns=["A", "B", "C"])
    pd.testing.assert_frame_equal(next(dfs), expected_first_df, check_dtype=False)

    expected_second_df = pd.DataFrame(data=[(np.NaN, 13, 12), (np.NaN, 15, 14)], columns=["A", "B", "C"])
    pd.testing.assert_frame_equal(next(dfs), expected_second_df, check_dtype=False)
