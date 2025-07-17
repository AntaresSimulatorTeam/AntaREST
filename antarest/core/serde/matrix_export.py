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
from typing import Iterator, Protocol

import pandas as pd
from typing_extensions import override

from antarest.study.business.enum_ignore_case import EnumIgnoreCase

try:
    import openpyxl  # noqa: F401
    import tables  # type: ignore # noqa: F401
    import xlsxwriter  # type: ignore # noqa: F401
except ImportError:
    raise ImportError("The 'xlsxwriter', 'openpyxl' and 'tables' packages are required") from None


class DataframeStreamWriter(Protocol):
    """
    A writer which can write down a partitioned table.

    This allows to not need to hold the full dataframe in memory, but only
    one chunk at a time.
    All provided dataframes must have same columns.
    """

    def __call__(self, path: Path, dataframes: Iterator[pd.DataFrame]) -> None: ...


def _checked_dataframes_generator(dataframes: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    """
    Checks consistency between subsequent dataframes
    """
    columns = None
    for df in dataframes:
        if df.empty:
            continue
        if columns is None:
            columns = df.columns
        else:
            if any(columns != df.columns):
                raise ValueError("Cannot append dataframe to file, columns are different from initial dataframe.")
        yield df


def _write_dataframes_stream_csv(path: Path, sep: str, decimal: str, dataframes: Iterator[pd.DataFrame]) -> None:
    headers = True
    append = False
    for df in _checked_dataframes_generator(dataframes):
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
    for df in _checked_dataframes_generator(dataframes):
        with pd.ExcelWriter(
            path, mode="w" if is_first else "a", if_sheet_exists=None if is_first else "overlay", engine="openpyxl"
        ) as writer:
            df.to_excel(writer, index=False, header=is_first, startcol=0, startrow=row)
        row += df.shape[0]
        if is_first:  # account for headers
            row += 1
        is_first = False


def _write_dataframes_stream_hdf5(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
    append = False
    for df in _checked_dataframes_generator(dataframes):
        df.to_hdf(path, key="data", append=append, index=False, format="table", mode="r+" if append else "w")
        append = True


class TableExportFormat(EnumIgnoreCase):
    """Export format for tables."""

    XLSX = "xlsx"
    HDF5 = "hdf5"
    TSV = "tsv"
    CSV = "csv"
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
            case TableExportFormat.HDF5:
                return "application/x-hdf5"
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
            case TableExportFormat.HDF5:
                return ".h5"
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
            case TableExportFormat.HDF5:
                return _write_dataframes_stream_hdf5
            case _:
                raise NotImplementedError(f"Export format '{self}' does not support stream writing.")

    def export_table(
        self,
        df: pd.DataFrame,
        export_path: str | Path,
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
            case TableExportFormat.HDF5:
                return df.to_hdf(
                    export_path,
                    key="data",
                    mode="w",
                    format="table",
                    data_columns=True,
                )
            case _:
                raise NotImplementedError(f"Export format '{self}' is not implemented")
