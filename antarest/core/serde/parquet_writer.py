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
        write_page_index=True,
        compression="zstd",
        data_page_version="2.0",
        sorting_columns=[],
    )


def write_dataframes_in_parquet_format(path: Path, dataframes: Iterator[pd.DataFrame]) -> set[str]:
    writers = {}
    file_counter = 0
    filenames = set()

    for df, new_file_to_write in _check_dataframes_columns_consistency(dataframes):
        df_cols = tuple(df.columns)

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

    return filenames


def yield_dataframes_to_write(path: Path, dataframes: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    all_df_names = write_dataframes_in_parquet_format(path, dataframes)
    all_cols: set[str] = set()
    for df_name in all_df_names:
        parquet_file = ParquetFile(path / df_name)
        table = parquet_file.read_row_group(0)
        all_cols.update(table.column_names)

    for df_name in all_df_names:
        parquet_file = ParquetFile(path / df_name)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            missing_cols = all_cols - set(df.columns)
            for col in missing_cols:
                df[col] = None
            yield df


def _check_dataframes_columns_consistency(dataframes: Iterator[pd.DataFrame]) -> Iterator[tuple[pd.DataFrame, bool]]:
    existing_columns: set[str] = set()
    for df in dataframes:
        should_write_new_file = False
        if df.empty:
            continue
        if not existing_columns:
            existing_columns = set(df.columns)
        else:
            df_cols = set(df.columns)
            if existing_columns != df_cols:
                if df_cols - existing_columns:
                    # Means we have to add new columns to the existing dataframe
                    should_write_new_file = True
                else:
                    # Means we only have to add mising columns inside the current dataframe
                    columns_to_add = existing_columns - df_cols
                    for col in columns_to_add:
                        df[col] = None
                existing_columns.update(df_cols)

        yield df, should_write_new_file
