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

import pandas as pd
import pytest

from antarest.core.serde.matrix_export import TableExportFormat, _checked_dataframes_generator


def test_checked_stream_removes_empty_dataframes():
    dfs = [
        pd.DataFrame(),
        pd.DataFrame(data=[(12, 13), (14, 15)], columns=["A", "B"]),
    ]
    as_list = [d for d in _checked_dataframes_generator(iter(dfs))]
    assert len(as_list) == 1

    dfs = [
        pd.DataFrame(data=[(12, 13), (14, 15)], columns=["A", "B"]),
        pd.DataFrame(),
    ]
    as_list = [d for d in _checked_dataframes_generator(iter(dfs))]
    assert len(as_list) == 1


def test_checked_stream_provides_valid_dataframes():
    dfs = [
        pd.DataFrame(data=[(10, 11), (12, 13)], columns=["A", "B"]),
        pd.DataFrame(data=[(12, 13), (14, 15)], columns=["A", "B"]),
    ]
    as_list = [d for d in _checked_dataframes_generator(iter(dfs))]
    assert len(as_list) == 2


def test_checked_stream_raises_on_different_columns():
    dfs = [
        pd.DataFrame(data=[(10, 11), (12, 13)], columns=["A", "B"]),
        pd.DataFrame(data=[(12, 13), (14, 15)], columns=["B", "C"]),
    ]
    with pytest.raises(ValueError, match="columns are different"):
        [d for d in _checked_dataframes_generator(iter(dfs))]


@pytest.fixture
def dataframes() -> Iterator[pd.DataFrame]:
    return iter(
        [
            pd.DataFrame(data=[(10, 11), (12, 13)], columns=["A", "B"]),
            pd.DataFrame(data=[(12, 13), (14, 15)], columns=["A", "B"]),
        ]
    )


@pytest.fixture
def expected_concatenation() -> pd.DataFrame:
    return pd.DataFrame(data=[(10, 11), (12, 13), (12, 13), (14, 15)], columns=["A", "B"])


@pytest.mark.parametrize(
    "format,expected_delimiter",
    [
        (TableExportFormat.CSV, ","),
        (TableExportFormat.TSV, "\t"),
        (TableExportFormat.CSV_SEMICOLON, ";"),
    ],
)
def test_csv_stream_writer(
    tmp_path: Path,
    dataframes: Iterator[pd.DataFrame],
    format: TableExportFormat,
    expected_delimiter: str,
    expected_concatenation: pd.DataFrame,
) -> None:
    export_path = tmp_path / "export.csv"
    writer = format.get_stream_writer()
    writer(path=export_path, dataframes=dataframes)
    parsed = pd.read_csv(export_path, delimiter=expected_delimiter)

    pd.testing.assert_frame_equal(parsed, expected_concatenation)


def test_excel_stream_writer(tmp_path: Path, dataframes: Iterator[pd.DataFrame], expected_concatenation: pd.DataFrame):
    export_path = tmp_path / "export.xlsx"
    writer = TableExportFormat.XLSX.get_stream_writer()
    writer(path=export_path, dataframes=dataframes)
    parsed = pd.read_excel(export_path)

    pd.testing.assert_frame_equal(parsed, expected_concatenation)


def test_hdf5_stream_writer(tmp_path: Path, dataframes: Iterator[pd.DataFrame], expected_concatenation: pd.DataFrame):
    export_path = tmp_path / "export.hdf5"
    writer = TableExportFormat.HDF5.get_stream_writer()
    writer(path=export_path, dataframes=dataframes)

    parsed = pd.read_hdf(export_path)
    parsed = parsed.reset_index(drop=True)

    pd.testing.assert_frame_equal(parsed, expected_concatenation)
