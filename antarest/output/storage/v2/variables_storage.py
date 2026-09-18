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
"""Write all output families with schemas defined by database metadata."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

import polars as pl
import polars.selectors as pls
import pyarrow as pa
from polars import Float64

from antarest.core.serde.parquet_writer import BatchParquetWriter
from antarest.output.filestudy.matrixfiles import get_start_column, parse_output_file
from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.dbmodel import ElementType, ScenarioAggregation
from antarest.output.storage.v2.layout import SourceFile, header_groups, index_columns, parquet_filename, source_files
from antarest.output.storage.v2.metadata import IParquetOutputMetadata
from antarest.study.model import MatrixFrequency

if TYPE_CHECKING:
    Field = pa.Field[Any]
else:
    Field = pa.Field

INDEX_FIELDS: dict[str, Field] = {
    "mcYear": pa.field("mcYear", pa.int32()),
    "timeId": pa.field("timeId", pa.int32()),
    **{key: pa.field(key, pa.large_string()) for key in ("area", "link", "cluster", "constraint")},
}


def parquet_output_dir(variables_dir: Path, study_id: str, output_name: str) -> Path:
    return variables_dir / f"{study_id}-{output_name}"


@dataclass(frozen=True)
class IndexedOutputDataFrame:
    """
    An output dataframe with columns for variables AND for "index" data such as the timestep, the element ID,
    the MC year.
    """

    index_cols: Sequence[str]
    var_cols: Sequence[VariableDescription]

    data: pl.DataFrame


class ParquetOutputWriter:
    """
    Utility class to append polars DF to a parquet file, taking care of adapting it to the required schema
    (list of columns), and grouping them in not too small row groups (through batch parquet writer).

    Columns are named after variables but mainly for debugging purpose: the source of truth for variable columns
    metadata remains the information stored in database.
    """

    def __init__(self, target_path: Path, index_cols: list[str], var_cols: Sequence[VariableDescription]) -> None:
        self.index_cols = index_cols
        self.var_cols = var_cols
        self.target_path = target_path
        self.writer: BatchParquetWriter | None = None
        # Names are diagnostic only. Disambiguate equal names/units/statistics safely.
        self.column_names: list[str] = []
        used = set(index_cols)
        for i, variable in enumerate(var_cols):
            name = variable.normal_repr()
            while name in used:
                name += f"__{i}"
            used.add(name)
            self.column_names.append(name)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        if self.writer:
            self.writer.close()

    def _create_schema(self) -> pa.Schema:
        return pa.schema(
            [INDEX_FIELDS[c] for c in self.index_cols]
            + [pa.field(self._col_name(i), pa.float64()) for i in range(len(self.var_cols))]
        )

    def _col_name(self, index: int) -> str:
        """
        Trying to have a meaningful naming mainly for debugging purpose.
        For business logic, the code MUST rely on database metadata instead.
        """
        return self.column_names[index]

    def _adapt_df(self, output_df: IndexedOutputDataFrame) -> pa.Table:
        offset = len(self.index_cols)
        col_for_variable = {v: offset + i for i, v in enumerate(output_df.var_cols)}
        nulls = pl.lit(None, dtype=Float64)
        # just keep the index cols as is (just enforcing the "right" name here
        index_cols = [pls.by_index(i).alias(name) for i, name in enumerate(self.index_cols)]
        # reorder var cols and insert nulls where missing
        var_cols = [
            pls.by_index(col_for_variable[v]).cast(dtype=Float64).alias(self._col_name(i))
            if v in col_for_variable
            else nulls.alias(self._col_name(i))
            for i, v in enumerate(self.var_cols)
        ]
        adapted = output_df.data.select(index_cols + var_cols)
        return adapted.to_arrow()

    def append_output_df(self, output_df: IndexedOutputDataFrame) -> None:
        if output_df.index_cols != self.index_cols:
            raise ValueError(
                f"Dataframe index differs from parquet file index ({output_df.index_cols} != {self.index_cols})"
            )
        if not self.writer:
            self.writer = BatchParquetWriter(self.target_path, schema=self._create_schema())
        self.writer.append_table(self._adapt_df(output_df))


def create_parquet_files(metadata: IParquetOutputMetadata, file_output: FileOutput, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    files: dict[tuple[ScenarioAggregation, ElementType, MatrixFrequency], list[SourceFile]] = defaultdict(list)
    for source in source_files(file_output):
        if source.element_type not in ("area_id", "link_id"):
            files[source.aggregation, source.element_type, source.frequency].append(source)
    # One writer at a time bounds the row-group buffers across output families/frequencies.
    for (aggregation, element_type, frequency), sources in files.items():
        indices = index_columns(aggregation, element_type)
        variables = metadata.get_variables(aggregation, element_type)
        with ParquetOutputWriter(
            target_dir / parquet_filename(aggregation, element_type, frequency), indices, variables
        ) as writer:
            for source in sources:
                output = parse_output_file(source.path, get_start_column(frequency))
                for group in header_groups(output.headers, element_type):
                    index_exprs: list[pl.Expr] = []
                    if aggregation == "mc-ind":
                        index_exprs.append(pl.lit(source.year, dtype=pl.Int32()).alias("mcYear"))
                    id_col = indices[1] if aggregation == "mc-ind" else indices[0]
                    index_exprs.append(pl.lit(source.element_id, dtype=pl.String()).alias(id_col))
                    if group.cluster_id is not None:
                        index_exprs.append(pl.lit(group.cluster_id, dtype=pl.String()).alias("cluster"))
                    index_exprs.append(pl.int_range(1, pl.len() + 1, dtype=pl.Int32()).alias("timeId"))
                    selected: list[pl.Expr] = [pls.by_index(i) for i in group.positions]
                    writer.append_output_df(
                        IndexedOutputDataFrame(
                            index_cols=indices,
                            var_cols=group.variables,
                            data=output.data.select(index_exprs + selected),
                        )
                    )
