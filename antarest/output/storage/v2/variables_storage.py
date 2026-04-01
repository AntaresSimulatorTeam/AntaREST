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

"""
Conversion of Antares output TSV files to parquet format.

Output structure: one parquet file per (mc_root, object_type, frequency) tuple.
Naming convention: {mc_root}_{object_type}_{frequency}.parquet
Example: mc-all_areas_hourly.parquet, mc-ind_thermal_clusters_daily.parquet
"""

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import polars as pl
import pyarrow.parquet as pq

from antarest.output.filestudy.aggregator_management import AggregatorManager
from antarest.output.filestudy.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    MultipleOutputHeaders,
    QueryFileType,
    get_output_object_type,
    get_start_column,
    normalize_df_column_names,
    parse_output_file, TIME_ID_COL, MCYEAR_COL,
)
from antarest.output.utils import find_mode_dir
from antarest.study.model import MatrixFrequency

logger = logging.getLogger(__name__)


def parquet_output_dir(variables_dir: Path, study_id: str, output_name: str) -> Path:
    return variables_dir / f"{study_id}-{output_name}"


def _parquet_file_name(mc_root: MCRoot, object_type: str, frequency: MatrixFrequency) -> str:
    return f"{mc_root.value}_{object_type}_{frequency.value}.parquet"


_SKIPPED_QUERY_FILES = {"id"}
"""Query file types that should not be converted to parquet (metadata files, not variable data)."""


def _discover_file_type_frequencies(
    folders: list[Path], file_type_class: type[QueryFileType]
) -> list[tuple[QueryFileType, MatrixFrequency]]:
    seen: set[tuple[str, str]] = set()
    result: list[tuple[QueryFileType, MatrixFrequency]] = []
    for folder in folders:
        for file in folder.iterdir():
            if not file.name.endswith(".txt"):
                continue
            parts = file.stem.split("-")
            freq_str = parts[-1]
            file_type_str = "-".join(parts[:-1])
            key = (file_type_str, freq_str)
            if key in seen:
                continue
            try:
                query_file = file_type_class(file_type_str)
                if query_file.value in _SKIPPED_QUERY_FILES:
                    continue
                frequency = MatrixFrequency(freq_str)
                seen.add(key)
                result.append((query_file, frequency))
            except ValueError:
                continue
    return result


def _aggregate_to_parquet(
    output_dir: Path,
    query_file: QueryFileType,
    frequency: MatrixFrequency,
    ids_to_consider: list[str],
    target_path: Path,
) -> None:
    manager = AggregatorManager(
        output_path=output_dir,
        query_file=query_file,
        frequency=frequency,
        ids_to_consider=ids_to_consider,
        columns_names=[],
        transform_columns_headers=True,
    )
    try:
        all_dfs = list(manager.aggregate_output_data())
    except Exception as e:
        logger.debug(f"Skipping {query_file.value}-{frequency.value}: {e}")
        return

    if not all_dfs:
        return

    combined = pl.concat(all_dfs)

    id_cols = [c for c in ["area", "link", MCYEAR_COL] if c in combined.columns]
    if id_cols:
        combined = combined.sort(id_cols)

    table = combined.to_arrow()
    sorting_columns = [
        pq.SortingColumn(table.schema.get_field_index(col)) for col in id_cols if col in table.schema.names
    ]
    pq.write_table(
        table,
        target_path,
        compression="zstd",
        row_group_size=60 * 1024,
        data_page_version="2.0",
        sorting_columns=sorting_columns,
    )
    logger.debug(f"Wrote {len(combined)} rows to {target_path.name}")


def _extract_areas(
    output_dir: Path,
    base_path: Path,
    mc_root: MCRoot,
    target_dir: Path,
) -> None:
    areas_path = base_path / "areas"
    if not areas_path.exists():
        return

    all_ids = [d.name for d in areas_path.iterdir() if d.is_dir()]
    area_ids = []
    district_ids = []

    for item in all_ids:
        if item.startswith("@"):
            district_ids.append(item)
        else:
            area_ids.append(item)

    file_type_class: type[QueryFileType] = MCIndAreasQueryFile if mc_root == MCRoot.MC_IND else MCAllAreasQueryFile

    ref_folders = [areas_path / a for a in all_ids]
    combos = _discover_file_type_frequencies(ref_folders, file_type_class)

    for query_file, frequency in combos:
        obj_type = get_output_object_type(query_file, is_link=False)
        if area_ids:
            file_name = _parquet_file_name(mc_root, obj_type, frequency)
            _aggregate_to_parquet(output_dir, query_file, frequency, area_ids, target_dir / file_name)

        # Districts
        if district_ids and query_file.value == "values":
            file_name = _parquet_file_name(mc_root, "districts", frequency)
            _aggregate_to_parquet(output_dir, query_file, frequency, district_ids, target_dir / file_name)


def _extract_links(
    output_dir: Path,
    base_path: Path,
    mc_root: MCRoot,
    target_dir: Path,
) -> None:
    links_path = base_path / "links"
    if not links_path.exists():
        return

    link_ids = [d.name for d in links_path.iterdir() if d.is_dir()]
    if not link_ids:
        return

    file_type_class: type[QueryFileType] = MCIndLinksQueryFile if mc_root == MCRoot.MC_IND else MCAllLinksQueryFile
    ref_folders = [links_path / lid for lid in link_ids]
    combos = _discover_file_type_frequencies(ref_folders, file_type_class)

    for query_file, frequency in combos:
        file_name = _parquet_file_name(mc_root, "links", frequency)
        _aggregate_to_parquet(output_dir, query_file, frequency, link_ids, target_dir / file_name)


def _extract_binding_constraints(
    base_path: Path,
    mc_root: MCRoot,
    target_dir: Path,
) -> None:
    bc_path = base_path / "binding_constraints"
    if not bc_path.exists():
        return

    for file in bc_path.iterdir():
        if not file.name.endswith(".txt"):
            continue
        freq_str = file.stem.split("-")[-1]
        try:
            frequency = MatrixFrequency(freq_str)
        except ValueError:
            continue

        start_col = get_start_column(frequency)
        try:
            output_data = parse_output_file(file, start_col)
        except Exception as e:
            logger.debug(f"Skipping binding constraint {file.name}: {e}")
            continue

        df = output_data.data
        headers = cast(MultipleOutputHeaders, output_data.headers)
        col_names = normalize_df_column_names(mc_root, headers)
        df.columns = col_names
        df = df.with_row_index(TIME_ID_COL, offset=1)

        if df.is_empty():
            continue

        file_name = _parquet_file_name(mc_root, "binding_constraints", frequency)
        table = df.to_arrow()
        sorting_columns = (
            [pq.SortingColumn(table.schema.get_field_index(TIME_ID_COL))] if TIME_ID_COL in table.schema.names else []
        )
        pq.write_table(
            table,
            target_dir / file_name,
            compression="zstd",
            row_group_size=60 * 1024,
            data_page_version="2.0",
            sorting_columns=sorting_columns,
        )
        logger.debug(f"Wrote {len(df)} rows to {file_name}")


def extract_output_to_parquet(output_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    mode_dir = find_mode_dir(output_dir)
    if mode_dir is None:
        logger.warning(f"No economy or adequacy directory found in {output_dir}")
        return

    for mc_root in (MCRoot.MC_IND, MCRoot.MC_ALL):
        mc_root_path = mode_dir / str(mc_root.value)
        if not mc_root_path.exists():
            continue

        # For mc-ind, use first MC year folder for structure discovery
        if mc_root == MCRoot.MC_IND:
            years = [d for d in mc_root_path.iterdir() if d.is_dir()]
            if not years:
                continue
            base_path = years[0]
        else:
            base_path = mc_root_path

        _extract_areas(output_dir, base_path, mc_root, target_dir)
        _extract_links(output_dir, base_path, mc_root, target_dir)
        _extract_binding_constraints(base_path, mc_root, target_dir)

    logger.info(f"Extracted output variables to parquet in {target_dir}")


_ID_COLUMNS = {"area", "link", MCYEAR_COL, TIME_ID_COL, "cluster"}
"""Columns that are not variable data but identification/index columns."""


def _mc_root_for_query_file(query_file: QueryFileType) -> MCRoot:
    if isinstance(query_file, (MCIndAreasQueryFile, MCIndLinksQueryFile)):
        return MCRoot.MC_IND
    return MCRoot.MC_ALL


def _filter_columns(
    schema_names: list[str],
    columns_names: Sequence[str],
    mc_root: MCRoot,
    is_details: bool,
) -> list[str]:
    lower_filters = [c.lower() for c in columns_names]
    selected = []
    for col in schema_names:
        if col in _ID_COLUMNS:
            selected.append(col)
        elif mc_root == MCRoot.MC_IND and not is_details:
            if col.lower() in lower_filters:
                selected.append(col)
        else:
            if any(f in col.lower() for f in lower_filters):
                selected.append(col)
    return selected


def _read_filtered(
    parquet_path: Path,
    id_col: str,
    ids: Sequence[str],
    mc_root: MCRoot,
    mc_years: Sequence[int] | None,
    columns_names: Sequence[str],
    is_details: bool,
) -> pl.DataFrame | None:
    """Read a parquet file with optional filtering on IDs, MC years, and columns."""
    if not parquet_path.exists():
        return None

    lazy = pl.scan_parquet(parquet_path)

    if ids:
        lazy = lazy.filter(pl.col(id_col).is_in(list(ids)))

    if mc_years and mc_root == MCRoot.MC_IND:
        lazy = lazy.filter(pl.col(MCYEAR_COL).is_in(list(mc_years)))

    if columns_names:
        schema_names = lazy.collect_schema().names()
        selected = _filter_columns(schema_names, columns_names, mc_root, is_details)
        lazy = lazy.select(selected)

    return lazy.collect()


def read_output_from_parquet(
    target_dir: Path,
    query_file: QueryFileType,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    columns_names: Sequence[str],
    mc_years: Sequence[int] | None,
) -> pl.DataFrame:
    """Read and filter output data from parquet files"""
    mc_root = _mc_root_for_query_file(query_file)
    is_link = isinstance(query_file, (MCIndLinksQueryFile, MCAllLinksQueryFile))
    is_details = "details" in query_file.value
    obj_type = get_output_object_type(query_file, is_link)
    id_col = "link" if is_link else "area"

    # Split areas vs districts
    if not is_link and ids_to_consider:
        district_ids = [i for i in ids_to_consider if i.startswith("@")]
        area_ids = [i for i in ids_to_consider if not i.startswith("@")]
    else:
        district_ids = []
        area_ids = list(ids_to_consider)

    dfs: list[pl.DataFrame] = []

    # Read main file (areas, links, or details)
    if area_ids or not ids_to_consider:
        parquet_path = target_dir / _parquet_file_name(mc_root, obj_type, frequency)
        df = _read_filtered(parquet_path, id_col, area_ids, mc_root, mc_years, columns_names, is_details)
        if df is not None and not df.is_empty():
            dfs.append(df)

    # Read districts file if needed
    if district_ids:
        parquet_path = target_dir / _parquet_file_name(mc_root, "districts", frequency)
        df = _read_filtered(parquet_path, id_col, district_ids, mc_root, mc_years, columns_names, is_details)
        if df is not None and not df.is_empty():
            dfs.append(df)

    if not dfs:
        return pl.DataFrame()

    return pl.concat(dfs)
