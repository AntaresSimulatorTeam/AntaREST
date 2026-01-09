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
from typing import IO, Iterator, Protocol

import numpy as np
import pandas as pd
import polars as pl
from typing_extensions import override

from antarest.core.serde.parquet_writer import write_dataframes_stream_parquet
from antarest.study.business.enum_ignore_case import EnumIgnoreCase

try:
    import openpyxl  # noqa: F401
    import tables  # type: ignore # noqa: F401
    import xlsxwriter  # type: ignore # noqa: F401
except ImportError:
    raise ImportError("The 'xlsxwriter', 'openpyxl' and 'tables' packages are required") from None


def simplify_dataframe(dataframe: pd.DataFrame, np_type: type[np.int32] | type[np.int64] = np.int64) -> pd.DataFrame:
    """
    Checks if the dataFrame could be represented with integer values.
    If so, returns it this way as it will be quicker to write or to return.
    """

    try:
        df_as_int = dataframe.astype(np_type)
        pd.testing.assert_frame_equal(dataframe, df_as_int, check_dtype=False, check_exact=True)
        return df_as_int
    except Exception:
        return dataframe


def write_dataframe_in_tsv_format(df: pd.DataFrame, path: Path, headers: bool = False) -> None:
    df = simplify_dataframe(df)
    pl.from_pandas(df).write_csv(path, separator="\t", include_header=headers)


class DataframeStreamWriter(Protocol):
    """
    A writer which can write down a partitioned table.

    This allows to not need to hold the full dataframe in memory, but only
    one chunk at a time.
    All provided dataframes must have same columns.
    """

    def __call__(self, path: Path, dataframes: Iterator[pd.DataFrame]) -> None: ...


def _write_dataframes_stream_csv(path: Path, sep: str, decimal: str, dataframes: Iterator[pd.DataFrame]) -> None:
    headers = True
    append = False
    for df in dataframes:
        df.to_csv(path, mode="a" if append else "w", sep=sep, decimal=decimal, index=False, header=headers)
        headers = False
        append = True


def _csv_stream_writer(sep: str, decimal: str) -> DataframeStreamWriter:
    def writer(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
        _write_dataframes_stream_csv(path, sep, decimal, dataframes)

    return writer


def _write_dataframes_stream_excel(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
    row = 0
    is_first = True
    for df in dataframes:
        with pd.ExcelWriter(
            path, mode="w" if is_first else "a", if_sheet_exists=None if is_first else "overlay", engine="openpyxl"
        ) as writer:
            df.to_excel(writer, index=False, header=is_first, startcol=0, startrow=row)
        row += df.shape[0]
        if is_first:  # account for headers
            row += 1
        is_first = False


class TableExportFormat(EnumIgnoreCase):
    """Export format for tables."""

    XLSX = "xlsx"
    TSV = "tsv"
    CSV = "csv"
    PARQUET = "parquet"
    CSV_SEMICOLON = "csv (semicolon)"

    @override
    def __str__(self) -> str:
        """Return the format as a string for display."""
        return self.value.title()

    @property
    def media_type(self) -> str:
        """Return the media type used for the HTTP response."""
        match self:
            case TableExportFormat.XLSX:
                # noinspection SpellCheckingInspection
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            case TableExportFormat.TSV:
                return "text/tab-separated-values"
            case TableExportFormat.CSV | TableExportFormat.CSV_SEMICOLON:
                return "text/csv"
            case TableExportFormat.PARQUET:
                return "application/vnd.apache.parquet"
            case _:
                raise NotImplementedError(f"Export format '{self}' is not implemented")

    @property
    def suffix(self) -> str:
        """Return the file suffix for the format."""
        match self:
            case TableExportFormat.XLSX:
                return ".xlsx"
            case TableExportFormat.TSV:
                return ".tsv"
            case TableExportFormat.CSV | TableExportFormat.CSV_SEMICOLON:
                return ".csv"
            case TableExportFormat.PARQUET:
                return ".parquet"
            case _:
                raise NotImplementedError(f"Export format '{self}' is not implemented")

    def get_stream_writer(self) -> DataframeStreamWriter:
        match self:
            case TableExportFormat.XLSX:
                return _write_dataframes_stream_excel
            case TableExportFormat.CSV:
                return _csv_stream_writer(sep=",", decimal=".")
            case TableExportFormat.CSV_SEMICOLON:
                return _csv_stream_writer(sep=";", decimal=",")
            case TableExportFormat.TSV:
                return _csv_stream_writer(sep="\t", decimal=".")
            case TableExportFormat.PARQUET:
                return write_dataframes_stream_parquet
            case _:
                raise NotImplementedError(f"Export format '{self}' does not support stream writing.")

    def export_table(
        self,
        df: pd.DataFrame,
        export_path: str | Path | IO[bytes],
        *,
        with_index: bool = True,
        with_header: bool = True,
    ) -> None:
        """Export a table to a file in the given format."""
        match self:
            case TableExportFormat.XLSX:
                return df.to_excel(
                    export_path,
                    index=with_index,
                    header=with_header,
                    engine="xlsxwriter",
                )
            case TableExportFormat.TSV:
                return df.to_csv(export_path, sep="\t", index=with_index, header=with_header)
            case TableExportFormat.CSV:
                return df.to_csv(export_path, sep=",", index=with_index, header=with_header)
            case TableExportFormat.CSV_SEMICOLON:
                return df.to_csv(export_path, sep=";", decimal=",", index=with_index, header=with_header)
            case TableExportFormat.PARQUET:
                return df.to_parquet(export_path, compression="zstd", index=with_index)
            case _:
                raise NotImplementedError(f"Export format '{self}' is not implemented")
