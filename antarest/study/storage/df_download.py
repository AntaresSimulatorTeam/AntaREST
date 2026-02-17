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
import http
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterator, TypeAlias

import pandas as pd
import polars as pl
from fastapi import HTTPException
from starlette.responses import FileResponse

from antarest.core.filetransfer.model import FileDownloadNotFound
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.serde.matrix_export import TableExportFormat
from antarest.core.serde.parquet_writer import (
    write_dataframes_in_parquet_format_by_column_sets,
    yield_dataframes_from_parquet,
)


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


def export_df_chunks(
    tmp_path: Path, file_download_path: Path, df_chunks: Iterator[pl.DataFrame], export_format: TableExportFormat
) -> None:
    """
    We need to harmonize all dataframes as we could be aggregating dataframes with different columns.
    But we cannot perform a classic concatenation as we cannot hold all the dataframes in memory.
    So first, we're writing them in parquet files according to their columns.

    If only one file is created, it means all dataframes shared the same columns.
    If the user asked for `parquet` format, there's nothing more to do, we can use the created file as the response.

    Else, we'll have to iterate over written file(s), reading in chunks to avoid using too much memory and transforming them in the requested format.
    If there's several files, we also have to reindex the dataframes to fill missing columns and to share the same columns order.
    """

    with tempfile.TemporaryDirectory(dir=tmp_path) as working_dir_str:
        working_dir = Path(working_dir_str)
        files, all_cols = write_dataframes_in_parquet_format_by_column_sets(working_dir, df_chunks)

        new_index = all_cols
        if len(files) == 1:
            if export_format == TableExportFormat.PARQUET:
                shutil.move(files[0], file_download_path)
                return
            # No need to reindex as all dataframes have the same columns
            new_index = []

        stream_writer = export_format.get_stream_writer()
        stream_writer(file_download_path, yield_dataframes_from_parquet(files, new_index))
