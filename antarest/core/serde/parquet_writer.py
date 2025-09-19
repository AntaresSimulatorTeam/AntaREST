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
    file_name = "file1.parquet"
    all_df_paths = {file_name}

    for df, new_file_to_write in _check_dataframes_columns_consistency(dataframes):
        file_name = "file1.parquet"
        if new_file_to_write:
            file_name = f"file{len(all_df_paths) + 1}.parquet"
            all_df_paths.add(file_name)

        table = pa.Table.from_pandas(df)
        with _parquet_writer(path / file_name, table.schema) as writer:
            writer.write_table(table)

    return all_df_paths


def yield_dataframes_to_write(path: Path, dataframes: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    all_df_names = write_dataframes_in_parquet_format(path, dataframes)
    all_cols = set()
    for df_name in all_df_names:
        parquet_file = ParquetFile(path / df_name)
        table = parquet_file.read_row_group(0)
        all_cols.update(table.columns)
    df_with_all_cols = pd.DataFrame(columns=list(all_cols))

    for df_name in all_df_names:
        parquet_file = ParquetFile(path / df_name)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            yield pd.concat([df, df_with_all_cols])


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
