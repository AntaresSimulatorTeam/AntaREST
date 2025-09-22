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
    return ParquetWriter(
        output_file,
        schema,
        compression="zstd",
        data_page_version="2.0",
        sorting_columns=[],
    )


def write_dataframes_in_parquet_format(path: Path, dataframes: Iterator[pd.DataFrame]) -> tuple[set[str], set[str]]:
    writers = {}
    file_counter = 0
    filenames = set()
    existing_columns: set[str] = set()

    for df in dataframes:
        if df.empty:
            continue
        df_cols = tuple(df.columns)
        existing_columns.update(df_cols)

        df.index = pd.Index(range(len(df)))
        table = pa.Table.from_pandas(df)

        if df_cols not in writers:
            file_name = f"file{file_counter}.parquet"
            filenames.add(file_name)
            file_path = path / file_name
            file_counter += 1

            new_writer = _parquet_writer(file_path, table.schema)
            writers[df_cols] = new_writer

        writers[df_cols].write_table(table)

    # Close all writers
    for writer in writers.values():
        writer.close()

    return filenames, existing_columns


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


def yield_parquet_dataframes(folder_path: Path, all_df_names: set[str], all_cols: set[str]) -> Iterator[pd.DataFrame]:
    for df_name in all_df_names:
        parquet_file = ParquetFile(folder_path / df_name)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            missing_cols = all_cols - set(df.columns)
            for col in missing_cols:
                df[col] = None
            yield df
