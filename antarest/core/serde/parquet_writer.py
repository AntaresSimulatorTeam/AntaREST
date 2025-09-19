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

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow as pa
from pyarrow.parquet import ParquetWriter, SortingColumn


@dataclass
class ParquetOptions:
    """
    Options for writing parquet files.

    Attributes:
        row_group_size: The number of rows in each row group. Default 64k, found to be performant for later queries,
                        compared to 1024k which is the default batch size of pyarrow.
    """

    row_group_size: int = 64 * 1024
    use_dict: bool = True
    use_bss: bool = False
    write_page_index: bool = True
    sorting_columns: list[SortingColumn] | None = None


def _parquet_writer(
    output_file: Path,
    schema: pa.Schema,
    parquet_options: ParquetOptions | None = None,
) -> ParquetWriter:
    options = parquet_options or ParquetOptions()
    return ParquetWriter(
        output_file,
        schema,
        write_page_index=options.write_page_index,
        use_dictionary=options.use_dict,
        use_byte_stream_split=options.use_bss,
        compression="zstd",
        data_page_version="2.0",
        sorting_columns=options.sorting_columns or [],
    )


def _concatenate_dataframes(
    dataframes: Iterable[pd.DataFrame], target_batch_size: int = 64 * 1024
) -> Iterable[pa.Table]:
    current_batch = []
    current_batch_size = 0

    for df in dataframes:
        next_size = current_batch_size + len(df)
        if next_size <= target_batch_size:
            current_batch.append(df)
            current_batch_size = next_size
        else:
            additional_rows = target_batch_size - current_batch_size
            current_batch.append(df.head(additional_rows))

            yield pa.Table.from_batches([pa.RecordBatch.from_pandas(df) for df in current_batch])
            first_df: pd.DataFrame = df.iloc[additional_rows:]
            current_batch = [first_df]
            current_batch_size = len(first_df)

    if current_batch:
        yield pa.Table.from_batches([pa.RecordBatch.from_pandas(df) for df in current_batch])


def write_dataframes_to_parquet(
    dataframes: Iterable[pd.DataFrame],
    output_file: Path,
    parquet_options: ParquetOptions,
) -> None:
    """
    Write multiple dataframes into one parquet file.
    """
    if output_file.exists():
        raise ValueError(f"{output_file} already exists")
    tables = _concatenate_dataframes(dataframes, parquet_options.row_group_size)
    table_iterator = iter(tables)
    try:
        first_table = next(table_iterator)
    except StopIteration:
        raise ValueError("No dataframe provided")

    with _parquet_writer(
        output_file,
        first_table.schema,
        parquet_options,
    ) as writer:
        writer.write_table(first_table, row_group_size=parquet_options.row_group_size)

        while True:
            try:
                next_table = next(table_iterator)
            except StopIteration:
                break
            writer.write_table(next_table, row_group_size=parquet_options.row_group_size)
