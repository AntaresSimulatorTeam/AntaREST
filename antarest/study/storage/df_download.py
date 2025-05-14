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

    export_file_download = file_transfer_manager.request_download(
        download_name,
        download_log,
        use_notification=False,
        expiration_time_in_minutes=10,
    )
    export_path = Path(export_file_download.path)
    export_id = export_file_download.id

    try:
        export_format.export_table(df_matrix, export_path, with_index=with_index, with_header=with_header)
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
            "Content-Type": f"{export_format.media_type}; charset=utf-8",
        },
        media_type=export_format.media_type,
    )
