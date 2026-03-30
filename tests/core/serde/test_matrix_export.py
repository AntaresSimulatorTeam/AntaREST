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

import pandas as pd
import pytest

from antarest.core.serde.matrix_export import TableExportFormat


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


def test_excel_stream_writer(
    tmp_path: Path, dataframes: Iterator[pd.DataFrame], expected_concatenation: pd.DataFrame
) -> None:
    export_path = tmp_path / "export.xlsx"
    writer = TableExportFormat.XLSX.get_stream_writer()
    writer(path=export_path, dataframes=dataframes)
    parsed = pd.read_excel(export_path)

    pd.testing.assert_frame_equal(parsed, expected_concatenation)


def test_parquet_stream_writer(
    tmp_path: Path, dataframes: Iterator[pd.DataFrame], expected_concatenation: pd.DataFrame
) -> None:
    export_path = tmp_path / "export.parquet"
    writer = TableExportFormat.PARQUET.get_stream_writer()
    writer(path=export_path, dataframes=dataframes)

    parsed = pd.read_parquet(export_path)

    pd.testing.assert_frame_equal(parsed, expected_concatenation)
