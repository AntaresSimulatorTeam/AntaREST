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
import shutil
import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import cast

import polars as pl

from antarest.core.exceptions import MCRootNotHandled, OutputAggregationError, OutputNotFound, OutputSubFolderNotFound
from antarest.core.serde.parquet_writer import (
    write_dataframes_in_parquet_format_by_column_sets,
    write_dataframes_stream_parquet,
    yield_dataframes_from_parquet,
)
from antarest.output.filestudy.aggregation import iterate_output_matrices
from antarest.output.filestudy.utils import (
    MCYEAR_COL,
    TIME_ID_COL,
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    get_output_object_type,
    get_start_column,
    parse_output_file,
)
from antarest.output.model import ClusterVarColumn, OutputColumn, OutputTable, VarColumn
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


def _merge_intermediate_parquets(file_paths: list[Path], new_index: list[str], target_path: Path) -> None:
    if len(file_paths) == 1:
        shutil.move(file_paths[0], target_path)
        return
    dataframes = yield_dataframes_from_parquet(file_paths, new_index)
    write_dataframes_stream_parquet(target_path, dataframes)


def _aggregate_to_parquet(
    output_dir: Path,
    query_file: QueryFileType,
    frequency: MatrixFrequency,
    ids_to_consider: list[str],
    target_path: Path,
) -> None:
    try:
        matrices = iterate_output_matrices(
            output_path=output_dir,
            query_file=query_file,
            frequency=frequency,
            ids_to_consider=ids_to_consider,
            columns_names=[],
        )
        dataframes = map(lambda m: m.to_polars(serialize_column_metadata), matrices)
    except (OutputNotFound, OutputSubFolderNotFound, OutputAggregationError, MCRootNotHandled) as e:
        logger.warning(f"Skipping {query_file.value}-{frequency.value}: {e}")
        return

    with tempfile.TemporaryDirectory() as intermediate_dir:
        file_paths, new_index = write_dataframes_in_parquet_format_by_column_sets(Path(intermediate_dir), dataframes)
        if not file_paths:
            return
        _merge_intermediate_parquets(file_paths, new_index, target_path)


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


def _parse_bc_file(file: Path, mc_year: int | None = None) -> pl.DataFrame | None:
    freq_str = file.stem.split("-")[-1]
    try:
        frequency = MatrixFrequency(freq_str)
    except ValueError:
        return None

    start_col = get_start_column(frequency)
    try:
        output_table = parse_output_file(file, start_col)
    except Exception as e:
        logger.debug(f"Skipping binding constraint {file.name}: {e}")
        return None

    df = output_table.data.with_row_index(TIME_ID_COL, offset=1)

    if mc_year is not None:
        df = df.with_columns(pl.lit(mc_year).alias(MCYEAR_COL))

    return df if not df.is_empty() else None


def _discover_bc_frequencies(bc_path: Path) -> set[str]:
    freqs: set[str] = set()
    for file in bc_path.iterdir():
        if file.name.endswith(".txt"):
            freqs.add(file.stem.split("-")[-1])
    return freqs


def _generate_bc_dataframes(
    bc_paths: list[tuple[Path, int | None]],
    freq_str: str,
) -> Iterator[pl.DataFrame]:
    for bc_path, mc_year in bc_paths:
        for file in bc_path.iterdir():
            if not file.name.endswith(".txt"):
                continue
            if file.stem.split("-")[-1] != freq_str:
                continue
            df = _parse_bc_file(file, mc_year)
            if df is not None:
                yield df


def _extract_binding_constraints(
    mc_root_path: Path,
    mc_root: MCRoot,
    target_dir: Path,
) -> None:
    bc_paths: list[tuple[Path, int | None]] = []
    if mc_root == MCRoot.MC_IND:
        for year_dir in sorted(mc_root_path.iterdir()):
            if not year_dir.is_dir():
                continue
            bc_path = year_dir / "binding_constraints"
            if bc_path.exists():
                bc_paths.append((bc_path, int(year_dir.name)))
    else:
        bc_path = mc_root_path / "binding_constraints"
        if bc_path.exists():
            bc_paths.append((bc_path, None))

    if not bc_paths:
        return

    # Discover all available frequencies
    all_freqs: set[str] = set()
    for bc_path, _ in bc_paths:
        all_freqs |= _discover_bc_frequencies(bc_path)

    for freq_str in all_freqs:
        try:
            frequency = MatrixFrequency(freq_str)
        except ValueError:
            continue

        file_name = _parquet_file_name(mc_root, "binding_constraints", frequency)
        intermediate_dir = Path(tempfile.mkdtemp())
        try:
            dataframes = _generate_bc_dataframes(bc_paths, freq_str)
            file_paths, new_index = write_dataframes_in_parquet_format_by_column_sets(intermediate_dir, dataframes)
            if file_paths:
                _merge_intermediate_parquets(file_paths, new_index, target_dir / file_name)
        finally:
            shutil.rmtree(intermediate_dir, ignore_errors=True)


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
        _extract_binding_constraints(mc_root_path, mc_root, target_dir)

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
) -> list[str]:
    lower_case_filters = [c.lower() for c in columns_names]

    def passes_filter(name: str) -> bool:
        # TODO:
        # This logic seems nonsense, and is not even in line with R package antaresRead.
        # Should probably be broken to get simpler ?
        col = parse_column_metadata(name)
        match col:
            case ClusterVarColumn(variable=var):
                return any(f in var.lower() for f in lower_case_filters)
            case VarColumn(variable=var, stat=stat):
                if stat:
                    return any(f in var.lower() for f in lower_case_filters)
                else:
                    return var.lower() in lower_case_filters
            case _:
                return True

    return list(filter(passes_filter, schema_names))


def _read_filtered(
    parquet_path: Path,
    id_col: str,
    ids: Sequence[str],
    mc_root: MCRoot,
    mc_years: Sequence[int] | None,
    columns_names: Sequence[str],
    is_details: bool,
) -> Iterator[pl.DataFrame]:
    if not parquet_path.exists():
        return

    lazy = pl.scan_parquet(parquet_path)

    if ids:
        lazy = lazy.filter(pl.col(id_col).is_in(list(ids)))

    if mc_years and mc_root == MCRoot.MC_IND:
        lazy = lazy.filter(pl.col(MCYEAR_COL).is_in(list(mc_years)))

    if columns_names:
        schema_names = lazy.collect_schema().names()
        selected = _filter_columns(schema_names, columns_names)
        lazy = lazy.select(selected)

    yield from lazy.collect_batches()


METADATA_SEPARATOR = "__"


def serialize_column_metadata(column: OutputColumn) -> str:
    """
    Formats metadata to be stored as a string in parquet column header.
    """
    match column:
        case VarColumn():
            return METADATA_SEPARATOR.join((column.variable, column.unit, column.stat or ""))
        case ClusterVarColumn():
            return METADATA_SEPARATOR.join((column.variable, column.stat or ""))
        case _:
            return column


def parse_column_metadata(column: str) -> OutputColumn:
    """
    Parses metadata from parquet column header.
    """
    parts = str.split(column, METADATA_SEPARATOR)
    match parts:
        case [idx] if idx in {"area", "link", "mcYear", "timeId", "cluster"}:
            return cast(OutputColumn, idx)
        case [variable, stat]:
            return ClusterVarColumn(variable, stat)
        case [variable, unit, stat]:
            return VarColumn(variable, unit, stat)
        case _:
            raise ValueError(f"Invalid column metadata: {column}")


def _df_to_table(df: pl.DataFrame) -> OutputTable:
    columns = [parse_column_metadata(c) for c in df.columns]
    return OutputTable(data=df, columns=columns)


def read_output_from_parquet(
    target_dir: Path,
    query_file: QueryFileType,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    columns_names: Sequence[str],
    mc_years: Sequence[int] | None,
) -> Iterator[OutputTable]:
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

    # Read main file (areas, links, or details)
    if area_ids or not ids_to_consider:
        parquet_path = target_dir / _parquet_file_name(mc_root, obj_type, frequency)
        dataframes = _read_filtered(parquet_path, id_col, area_ids, mc_root, mc_years, columns_names, is_details)
        return map(_df_to_table, dataframes)

    # Read districts file if needed
    if district_ids:
        parquet_path = target_dir / _parquet_file_name(mc_root, "districts", frequency)
        dataframes = _read_filtered(parquet_path, id_col, district_ids, mc_root, mc_years, columns_names, is_details)
        return map(_df_to_table, dataframes)

    raise ValueError(f"Invalid ids_to_consider: {ids_to_consider}")
