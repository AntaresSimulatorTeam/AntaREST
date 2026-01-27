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
from typing import Iterator

import numpy as np
import pandas as pd

from antarest.core.serde.parquet_writer import (
    write_dataframes_in_parquet_format_by_column_sets,
    yield_dataframes_from_parquet,
)


def test_different_columns(tmp_path: Path) -> None:
    dataframes = iter(
        [
            pd.DataFrame(data=[(1, 2), (3, 4)], columns=["A", "B"]),
            pd.DataFrame(data=[(5, 6, 7), (8, 9, 10)], columns=["A", "B", "C"]),
            pd.DataFrame(data=[(11, 12), (13, 14)], columns=["A", "B"]),
            pd.DataFrame(data=[(15, 16, 17), (18, 19, 20)], columns=["B", "A", "D"]),
        ]
    )

    files, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert files == [
        tmp_path / "file0.parquet",
        tmp_path / "file1.parquet",
        tmp_path / "file2.parquet",
    ]
    # A and B keep same order as in first files
    assert all_cols == ["A", "B", "C", "D"]

    dfs = yield_dataframes_from_parquet(files, all_cols)

    # Ensures we kept the order we had in the iterator
    expected_first_df = pd.DataFrame(
        data=[(1, 2, np.nan, np.nan), (3, 4, np.nan, np.nan)], columns=["A", "B", "C", "D"]
    )
    pd.testing.assert_frame_equal(next(dfs), expected_first_df, check_dtype=False)

    expected_second_df = pd.DataFrame(data=[(5, 6, 7, np.nan), (8, 9, 10, np.nan)], columns=["A", "B", "C", "D"])
    pd.testing.assert_frame_equal(next(dfs), expected_second_df, check_dtype=False)

    expected_third_df = pd.DataFrame(
        data=[(11, 12, np.nan, np.nan), (13, 14, np.nan, np.nan)], columns=["A", "B", "C", "D"]
    )
    pd.testing.assert_frame_equal(next(dfs), expected_third_df, check_dtype=False)

    # values of A and B are correctly "inverted"
    expected_fourth_df = pd.DataFrame(data=[(16, 15, np.nan, 17), (19, 18, np.nan, 20)], columns=["A", "B", "C", "D"])
    pd.testing.assert_frame_equal(next(dfs), expected_fourth_df, check_dtype=False)


def test_same_columns(tmp_path: Path) -> None:
    df1 = pd.DataFrame(data=[(10, 11), (12, 13)], columns=["A", "B"])
    df2 = pd.DataFrame(data=[(12, 13), (14, 15)], columns=["A", "B"])
    dataframes = iter([df1, df2])

    files, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert files == [tmp_path / "file0.parquet"]
    assert all_cols == ["A", "B"]

    dfs = yield_dataframes_from_parquet(files, all_cols)

    pd.testing.assert_frame_equal(next(dfs), df1, check_dtype=False)
    pd.testing.assert_frame_equal(next(dfs), df2, check_dtype=False)


def test_no_dataframes_given(tmp_path: Path) -> None:
    # This case can happen when no column matched the ones given by the user
    dataframes: Iterator[pd.DataFrame] = iter([])

    all_df_names, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert all_df_names == []
    assert all_cols == []
