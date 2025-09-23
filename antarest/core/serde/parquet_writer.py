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
import pyarrow as pa
from pyarrow.parquet import ParquetFile, ParquetWriter


def _parquet_writer(output_file: Path, schema: pa.Schema) -> ParquetWriter:
    return ParquetWriter(output_file, schema, compression="zstd", data_page_version="2.0")


def write_dataframes_in_parquet_format_by_column_sets(
    path: Path, dataframes: Iterator[pd.DataFrame]
) -> tuple[set[str], list[str]]:
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
    writers = {}
    file_counter = 0
    filenames = set()
    existing_columns: set[str] = set()
    new_index: list[str] = []

    try:
        for df in dataframes:
            if df.empty:
                continue
            df_cols = tuple(df.columns)
            for col in df_cols:
                if col not in existing_columns:
                    new_index.append(col)

            df.index = pd.RangeIndex(len(df))
            table = pa.Table.from_pandas(df)

            if df_cols not in writers:
                file_name = f"file{file_counter}.parquet"
                filenames.add(file_name)
                file_path = path / file_name
                file_counter += 1

                new_writer = _parquet_writer(file_path, table.schema)
                writers[df_cols] = new_writer

            writers[df_cols].write_table(table)

        return filenames, new_index

    finally:
        # Close all writers
        for writer in writers.values():
            writer.close()


def write_dataframes_stream_parquet(path: Path, dataframes: Iterator[pd.DataFrame]) -> None:
    try:
        first_df = next(dataframes)
        first_table = pa.Table.from_pandas(first_df)
        schema = first_table.schema
    except StopIteration:
        raise ValueError("No dataframe provided")

    with _parquet_writer(path, schema) as writer:
        writer.write_table(first_table)
        for df in dataframes:
            if df.empty:
                continue

            table = pa.Table.from_pandas(df)
            writer.write_table(table)


def yield_parquet_dataframes(folder_path: Path, all_df_names: set[str], new_index: list[str]) -> Iterator[pd.DataFrame]:
    """
    Iterates over the written parquet files, reads them using chunks and reindex them if needed.

    Args:
        folder_path: The parent folder path containing the parquet files
        all_df_names: The names of every written parquet file
        new_index: The new index to use for the dataframes. If the list is empty, we don't reindex them.

    """
    for df_name in all_df_names:
        parquet_file = ParquetFile(folder_path / df_name)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            if new_index:
                df = df.reindex(new_index, axis="columns")
            yield df
