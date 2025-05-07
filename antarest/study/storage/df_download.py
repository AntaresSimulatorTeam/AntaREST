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
import http
from pathlib import Path
from typing import Callable, Iterator, Literal, Protocol, TypeAlias

import pandas as pd
from fastapi import HTTPException
from starlette.responses import FileResponse
from typing_extensions import override

from antarest.core.filetransfer.model import FileDownloadNotFound
from antarest.core.filetransfer.service import FileTransferManager
from antarest.study.business.enum_ignore_case import EnumIgnoreCase

try:
    import tables  # type: ignore # noqa: F401
    import xlsxwriter  # type: ignore # noqa: F401
except ImportError:
    raise ImportError("The 'xlsxwriter' and 'tables' packages are required") from None


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
        if columns is None:
            columns = df.columns
            if columns.empty:
                yield pd.DataFrame()
                break
        else:
            if any(columns != df.columns):
                raise ValueError("Cannot append dataframe to file, columns are different from initial dataframe.")
        yield df


def _write_dataframes_stream_csv(path: Path, sep: str, decimal: str, dataframes: Iterator[pd.DataFrame]) -> None:
    headers = True
    mode: Literal["w", "a"] = "w"
    for df in _checked_dataframes_generator(dataframes):
        df.to_csv(path, mode=mode, sep=sep, decimal=decimal, index=False, header=headers, float_format="%.6f")
        headers = False
        mode = "a"


def _csv_stream_writer(sep: str, decimal: str) -> DataframeStreamWriter:
    def writer(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
        _write_dataframes_stream_csv(path, sep, decimal, dataframes)

    return writer


def write_dataframes_stream_excel(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
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


def write_dataframes_stream_hdf5(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
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
        if self == TableExportFormat.XLSX:
            # noinspection SpellCheckingInspection
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif self == TableExportFormat.TSV:
            return "text/tab-separated-values"
        elif self in (TableExportFormat.CSV, TableExportFormat.CSV_SEMICOLON):
            return "text/csv"
        elif self == TableExportFormat.HDF5:
            return "application/x-hdf5"
        else:  # pragma: no cover
            raise NotImplementedError(f"Export format '{self}' is not implemented")

    @property
    def suffix(self) -> str:
        """Return the file suffix for the format."""
        if self == TableExportFormat.XLSX:
            return ".xlsx"
        elif self == TableExportFormat.TSV:
            return ".tsv"
        elif self in (TableExportFormat.CSV, TableExportFormat.CSV_SEMICOLON):
            return ".csv"
        elif self == TableExportFormat.HDF5:
            return ".h5"
        else:  # pragma: no cover
            raise NotImplementedError(f"Export format '{self}' is not implemented")

    def get_stream_writer(self) -> DataframeStreamWriter:
        match self:
            case TableExportFormat.XLSX:
                return write_dataframes_stream_excel
            case TableExportFormat.CSV:
                return _csv_stream_writer(sep=",", decimal=".")
            case TableExportFormat.CSV_SEMICOLON:
                return _csv_stream_writer(sep=";", decimal=",")
            case TableExportFormat.TSV:
                return _csv_stream_writer(sep="\t", decimal=".")
            case TableExportFormat.HDF5:
                return write_dataframes_stream_hdf5
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
        if self == TableExportFormat.XLSX:
            return df.to_excel(
                export_path,
                index=with_index,
                header=with_header,
                engine="xlsxwriter",
            )
        elif self == TableExportFormat.TSV:
            return df.to_csv(
                export_path,
                sep="\t",
                index=with_index,
                header=with_header,
                float_format="%.6f",
            )
        elif self == TableExportFormat.CSV:
            return df.to_csv(
                export_path,
                sep=",",
                index=with_index,
                header=with_header,
                float_format="%.6f",
            )
        elif self == TableExportFormat.CSV_SEMICOLON:
            return df.to_csv(
                export_path,
                sep=";",
                decimal=",",
                index=with_index,
                header=with_header,
                float_format="%.6f",
            )
        elif self == TableExportFormat.HDF5:
            return df.to_hdf(
                export_path,
                key="data",
                mode="w",
                format="table",
                data_columns=True,
            )
        else:  # pragma: no cover
            raise NotImplementedError(f"Export format '{self}' is not implemented")


def export_file(
    df_matrix: pd.DataFrame,
    file_transfer_manager: FileTransferManager,
    export_format: TableExportFormat,
    with_index: bool,
    with_header: bool,
    download_name: str,
    download_log: str,
) -> FileResponse:
    """
    Exports a DataFrame to a file in the specified format and prepares it for download.

    Args:
        df_matrix: The DataFrame to be exported.
        file_transfer_manager: The FileTransferManager instance to handle file transfer operations.
        export_format: The format in which the DataFrame should be exported.
        with_index: Whether to include the DataFrame's index in the exported file.
        with_header: Whether to include the DataFrame's header in the exported file.
        download_name: The name of the file to be downloaded (file name with suffix)
        download_log: The log message for the download operation for the end-user.

    Returns:
        A FileResponse object representing the file to be downloaded.

    Raises:
        HTTPException: If there is an error during the export operation.
    """

    def file_writer(path: Path) -> None:
        export_format.export_table(df_matrix, path, with_index=with_index, with_header=with_header)

    return _export_file(file_transfer_manager, download_name, download_log, 10, file_writer, export_format.media_type)


def export_df_chunks(
    df_chunks: Iterator[pd.DataFrame],
    file_transfer_manager: FileTransferManager,
    export_format: TableExportFormat,
    download_name: str,
    download_log: str,
) -> FileResponse:
    stream_writer = export_format.get_stream_writer()

    def file_writer(path: Path) -> None:
        stream_writer(path, df_chunks)

    return _export_file(file_transfer_manager, download_name, download_log, 10, file_writer, export_format.media_type)


FileWriter: TypeAlias = Callable[[Path], None]


def _export_file(
    file_transfer_manager: FileTransferManager,
    download_name: str,
    download_log: str,
    expiration_time_in_minutes: int,
    writer: FileWriter,
    media_type: str,
) -> FileResponse:
    """ """
    export_file_download = file_transfer_manager.request_download(
        download_name,
        download_log,
        use_notification=False,
        expiration_time_in_minutes=expiration_time_in_minutes,
    )
    export_path = Path(export_file_download.path)
    export_id = export_file_download.id

    try:
        writer(export_path)
        file_transfer_manager.set_ready(export_id, use_notification=False)
    except ValueError as e:
        file_transfer_manager.fail(export_id, str(e))
        raise HTTPException(
            status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Cannot replace '{export_path}' due to Excel policy: {e}",
        ) from e
    except FileDownloadNotFound as e:
        file_transfer_manager.fail(export_id, str(e))
        raise HTTPException(
            status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"The file download does not exist in database :{str(e)}",
        ) from e

    return FileResponse(
        export_path,
        headers={
            "Content-Disposition": f'attachment; filename="{export_file_download.filename}"',
            "Content-Type": f"{media_type}; charset=utf-8",
        },
        media_type=media_type,
    )
