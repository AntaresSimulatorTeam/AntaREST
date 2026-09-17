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
"""Read only columns actually present for the selected elements."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from antarest.output.filestudy.model import VariableDescription
from antarest.output.storage.v2.dbmodel import ElementType, ScenarioAggregation
from antarest.output.storage.v2.layout import index_columns, parquet_filename
from antarest.output.storage.v2.metadata import ElementVariables, IParquetOutputMetadata
from antarest.study.model import MatrixFrequency


@dataclass(frozen=True)
class ElementDataFrame:
    element: ElementVariables
    variables: Sequence[VariableDescription]
    positions: Sequence[int]
    data: pl.DataFrame


def iterate_element_dfs(
    metadata: IParquetOutputMetadata,
    parquet_dir: Path,
    aggregation: ScenarioAggregation,
    element_type: ElementType,
    frequency: MatrixFrequency,
    years: Sequence[int],
    elements: Sequence[str],
    columns: Sequence[str] = (),
) -> Iterable[ElementDataFrame]:
    members = metadata.get_elements(aggregation, element_type, frequency, years, elements)
    if not members:
        return
    variables = metadata.get_variables(aggregation, element_type)
    indices = index_columns(aggregation, element_type)
    frame = pl.scan_parquet(parquet_dir / parquet_filename(aggregation, element_type, frequency))
    # Physical names only locate columns by position, never determine their meaning.
    names = frame.collect_schema().names()
    id_col = indices[1] if aggregation == "mc-ind" else indices[0]
    for element in members:
        chosen = [
            (i, position)
            for i, position in zip(element.variables, element.positions)
            if not columns or (element.cluster_id or variables[i].name) in columns
        ]
        if not chosen:
            continue
        selected = frame.filter(pl.col(id_col) == element.element_id)
        if aggregation == "mc-ind":
            selected = selected.filter(pl.col("mcYear") == element.year)
        if element.cluster_id is not None:
            selected = selected.filter(pl.col("cluster") == element.cluster_id)
        data = selected.sort("timeId").select([names[len(indices) + i] for i, _ in chosen]).collect()
        if data.is_empty():
            continue
        yield ElementDataFrame(element, [variables[i] for i, _ in chosen], [p for _, p in chosen], data)


@dataclass(frozen=True)
class AreaDataFrame:
    year: int
    area_id: str
    variables: Sequence[VariableDescription]
    data: pl.DataFrame


def iterate_areas_df(
    output_metadata: IParquetOutputMetadata,
    parquet_dir: Path,
    frequency: MatrixFrequency,
    years: Sequence[int],
    areas: Sequence[str],
    columns: Sequence[str],
) -> Iterable[AreaDataFrame]:
    for item in iterate_element_dfs(output_metadata, parquet_dir, "mc-ind", "area", frequency, years, areas, columns):
        yield AreaDataFrame(item.element.year, item.element.element_id, item.variables, item.data)


def aggregate_data(
    metadata: IParquetOutputMetadata,
    parquet_dir: Path,
    aggregation: ScenarioAggregation,
    element_type: ElementType,
    frequency: MatrixFrequency,
    years: Sequence[int],
    elements: Sequence[str],
    columns: Sequence[str],
) -> Iterable[pl.DataFrame]:
    """Expose the existing aggregation column convention, resolved through metadata."""
    from antarest.output.storage.v2.layout import CLUSTER_TYPES

    is_cluster = element_type in CLUSTER_TYPES
    all_variables = metadata.get_variables(aggregation, element_type)
    # Aggregation returns a rectangular union; missing variables remain null.
    names = []
    used: set[str] = set()
    for i, variable in enumerate(all_variables):
        name = variable.name if is_cluster else variable.normal_repr()
        while name in used:
            name += f"__{i}"
        names.append(name)
        used.add(name)
    filters = [c.lower() for c in columns]
    selected = [
        i
        for i, name in enumerate(names)
        if not filters
        or (any(f in name.lower() for f in filters) if aggregation == "mc-all" else name.lower() in filters)
    ]
    if is_cluster:
        selected.sort(key=lambda i: names[i])
    id_col = "link" if element_type == "link" else "area"
    for item in iterate_element_dfs(metadata, parquet_dir, aggregation, element_type, frequency, years, elements):
        member = item.element
        present = {v: i for i, v in enumerate(member.variables)}
        exprs = [pl.lit(member.element_id).alias(id_col)]
        if is_cluster:
            exprs.append(pl.lit(member.cluster_id).alias("cluster"))
        if aggregation == "mc-ind":
            exprs.append(pl.lit(member.year, dtype=pl.Int32()).alias("mcYear"))
        exprs.append(pl.int_range(1, pl.len() + 1, dtype=pl.Int32()).alias("timeId"))
        exprs.extend(
            (pl.col(item.data.columns[present[i]]) if i in present else pl.lit(None, dtype=pl.Float64)).alias(names[i])
            for i in selected
        )
        yield item.data.select(exprs)
