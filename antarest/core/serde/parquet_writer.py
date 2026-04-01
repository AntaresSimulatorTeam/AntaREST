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
from typing import Any, Literal

import pandas as pd
import polars as pl
import pyarrow as pa
from pyarrow.parquet import ParquetFile, ParquetWriter

from antarest.output.filestudy.utils import MCYEAR_COL, TIME_ID_COL

# 1M rows, which is the default in pyarrow parquet too
DEFAULT_ROW_GROUP_SIZE = 1024 * 1024
# Best performance/compression ratio
PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
# Could probably use 2.4 or 2.6 if we need
PARQUET_DATA_PAGE_VERSION: Literal["2.0"] = "2.0"


class BatchParquetWriter:
    """
    Wrapper around a plain parquet writer to ensure we write row groups of at least some target size.

    It's very important to use not too small row groups, in order to:
     - have efficient IO
     - avoid excessive memory usage for metadata (as shown by experienced)

    """

    def __init__(self, output_file: Path, schema: pa.Schema, row_group_size: int = DEFAULT_ROW_GROUP_SIZE):
        self._row_group_size = row_group_size
        self._writer = ParquetWriter(
            output_file, schema, compression=PARQUET_COMPRESSION, data_page_version=PARQUET_DATA_PAGE_VERSION
        )

        self._current_batch: list[pa.Table] = []
        self._current_batch_size = 0
        self._closed = False

    def __enter__(self) -> "BatchParquetWriter":
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.close()

    def add_table(self, table: pa.Table) -> None:
        if self._closed:
            raise ValueError("Writer is closed")
        self._current_batch.append(table)
        self._current_batch_size += table.num_rows
        if self._current_batch_size >= self._row_group_size:
            self._write_tables()

    def _write_tables(self) -> None:
        if self._current_batch:
            self._writer.write_table(pa.concat_tables(self._current_batch))
            self._current_batch = []
            self._current_batch_size = 0

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._write_tables()
        finally:
            self._writer.close()
            self._closed = True


def _adapt_polars_schema(df: pl.DataFrame) -> pl.DataFrame:
    # We have to use Float64 as a schema because if it differs the writing will fail.
    return df.with_columns(pl.selectors.numeric().exclude([MCYEAR_COL, TIME_ID_COL]).cast(pl.Float64))


def write_dataframes_in_parquet_format_by_column_sets(
    path: Path, dataframes: Iterator[pl.DataFrame]
) -> tuple[list[Path], list[str]]:
    """
    Iterates over the given dataframes and writes them according to their given column sets.
    If 2 dataframes share the same columns, we write them in the same file.
    Everytime we encounter a new column sets, we create a new parquet file.

    Args:
        path: The parent folder path to write the parquet files into.
        dataframes: The dataframes to iterate over.

    Returns:
        A tuple containing:
        1- A list of all created parquet files
        2- The list of every column encountered in the given dataframes. To use when reindexing the dataframes.
    """
    file_paths = []
    current_writer = None
    try:
        first_df = next(dataframes)
        new_index = list(first_df.columns)
        existing_columns = set(new_index)

        file_path = path / "file0.parquet"
        file_paths.append(file_path)
        file_counter = 1

        first_df = _adapt_polars_schema(first_df)
        table = first_df.to_arrow()
        current_writer = BatchParquetWriter(file_path, table.schema)
        current_writer.add_table(table)

        while True:
            try:
                df = next(dataframes)
                should_write_new_file = False
                for col in df.columns:
                    if col not in existing_columns:
                        should_write_new_file = True
                        existing_columns.add(col)
                        new_index.append(col)

                if df.columns != new_index:
                    expr = pl.lit(None, dtype=pl.Float64)
                    df = df.select([pl.col(c) if c in df.columns else expr.alias(c) for c in new_index])

                df = _adapt_polars_schema(df)
                table = df.to_arrow()

                if should_write_new_file:
                    current_writer.close()

                    file_path = path / f"file{file_counter}.parquet"
                    file_paths.append(file_path)
                    file_counter += 1

                    current_writer = BatchParquetWriter(file_path, table.schema)

                current_writer.add_table(table)

            except StopIteration:
                return file_paths, new_index
    except StopIteration:
        return [], []
    finally:
        if current_writer:
            current_writer.close()


def yield_dataframes_from_parquet(files: list[Path], new_index: list[str]) -> Iterator[pd.DataFrame]:
    """
    Iterates over the written parquet files, reads them using chunks and reindex them if needed.

    Args:
        files: Parquet files to read from
        new_index: The new index to use for the dataframes. If the list is empty, we don't reindex them.
    """
    for file in files:
        parquet_file = ParquetFile(file)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            if new_index:
                df = df.reindex(new_index, axis="columns")
            yield df


def write_dataframes_stream_parquet(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
    try:
        first_df = next(dataframes)
        first_table = pa.Table.from_pandas(first_df)
        schema = first_table.schema
    except StopIteration:
        raise ValueError("No dataframe provided")

    with BatchParquetWriter(path, schema) as writer:
        writer.add_table(first_table)
        for df in dataframes:
            table = pa.Table.from_pandas(df)
            writer.add_table(table)
