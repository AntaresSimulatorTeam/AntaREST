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
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from antarest.core.serde.parquet_writer import (
    write_dataframes_in_parquet_format_by_column_sets,
    yield_dataframes_from_parquet,
)


def test_different_columns(tmp_path: Path) -> None:
    dataframes = iter(
        [
            pl.DataFrame(data=[(1, 2), (3, 4)], schema=["A", "B"], orient="row"),
            # will cause a new file creation with schema A,B,C
            pl.DataFrame(data=[(5, 6, 7), (8, 9, 10)], schema=["A", "B", "C"], orient="row"),
            pl.DataFrame(data=[(11, 12), (13, 14)], schema=["A", "B"], orient="row"),
            # will cause a new file creation with schema A,B,C,D
            pl.DataFrame(data=[(15, 16, 17), (18, 19, 20)], schema=["B", "A", "D"], orient="row"),
            pl.DataFrame(data=[(21, 22), (23, 24)], schema=["C", "D"], orient="row"),
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

    # values of C and D are correctly
    expected_fifth_df = pd.DataFrame(
        data=[(np.nan, np.nan, 21, 22), (np.nan, np.nan, 23, 24)], columns=["A", "B", "C", "D"]
    )
    pd.testing.assert_frame_equal(next(dfs), expected_fifth_df, check_dtype=False)


def test_same_columns(tmp_path: Path) -> None:
    df1 = pl.DataFrame(data=[(10, 11), (12, 13)], schema=["A", "B"])
    df2 = pl.DataFrame(data=[(12, 13), (14, 15)], schema=["A", "B"])
    dataframes = iter([df1, df2])

    files, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert files == [tmp_path / "file0.parquet"]
    assert all_cols == ["A", "B"]

    dfs = yield_dataframes_from_parquet(files, all_cols)

    pd.testing.assert_frame_equal(next(dfs), df1.to_pandas(), check_dtype=False)
    pd.testing.assert_frame_equal(next(dfs), df2.to_pandas(), check_dtype=False)


def test_no_dataframes_given(tmp_path: Path) -> None:
    # This case can happen when no column matched the ones given by the user
    dataframes: Iterator[pl.DataFrame] = iter([])

    all_df_names, all_cols = write_dataframes_in_parquet_format_by_column_sets(tmp_path, dataframes)
    assert all_df_names == []
    assert all_cols == []
