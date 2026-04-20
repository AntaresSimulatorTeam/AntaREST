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
import dataclasses
import logging
import warnings
from collections.abc import Iterator, MutableSequence, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

import polars as pl
import polars.selectors as cs

from antarest.core.exceptions import MCRootNotHandled, OutputNotFound, OutputSubFolderNotFound
from antarest.output.filestudy.utils import (
    MCRoot,
    get_start_column,
    parse_output_file,
)
from antarest.output.model import (
    ClusterVarColumn,
    LazyOutputTable,
    MCAllAreasData,
    MCAllLinksData,
    MCIndAreasData,
    MCIndLinksData,
    OutputColumn,
    OutputDataType,
    OutputTable,
    VarColumn,
)
from antarest.output.utils import find_mode_dir
from antarest.study.model import MatrixFrequency

# We use pandas.DataFrame.stack() without the `future_stack` keyword as its 2 times faster
# But it logs a FutureWarning every time so we silence it here.
warnings.simplefilter(action="ignore", category=FutureWarning)

# noinspection SpellCheckingInspection
AREA_COL = "area"
"""Column name for the area."""
LINK_COL = "link"
"""Column name for the link."""
CLUSTER_ID_COL = "cluster"
"""Column name for the cluster id."""
MC_YEAR_INDEX = 0
"""Index in path parts starting from the Monte Carlo year to determine the Monte Carlo year."""
AREA_OR_LINK_INDEX__IND, AREA_OR_LINK_INDEX__ALL = 2, 1
"""Indexes in path parts starting from the output root `economy//mc-(ind/all)` to determine the area/link name."""
CLUSTER_ID_COMPONENT = 0
ACTUAL_COLUMN_COMPONENT = 1

logger = logging.getLogger(__name__)


def _filtered_files_listing(
    folders_to_check: list[Path],
    query_file: str,
    frequency: str,
) -> dict[str, MutableSequence[str]]:
    filtered_files: dict[str, MutableSequence[str]] = {}
    for folder_path in folders_to_check:
        for file in folder_path.iterdir():
            if file.stem == f"{query_file}-{frequency}":
                filtered_files.setdefault(folder_path.name, []).append(file.name)
    return filtered_files


@dataclass(frozen=True, order=True)
class OutputFile:
    path: Path
    year: int | None
    location: str


def _filter_files(folder_path: Path, ids: set[str]) -> list[str]:
    # Areas names filtering
    filtered = sorted([d.name for d in folder_path.iterdir()])
    if not ids:
        return filtered
    return [i for i in filtered if i in ids]


def identify_mc_ind_files(
    output_path: Path,
    query_file: MCIndAreasData | MCIndLinksData,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    mc_years: Sequence[int] | None,
) -> list[OutputFile]:
    mode_dir = find_mode_dir(output_path)
    if mode_dir is None:
        raise OutputSubFolderNotFound(output_path.name, f"economy/{MCRoot.MC_IND.value}")
    mc_ind_path = mode_dir / MCRoot.MC_IND.value
    output_type = "areas" if isinstance(query_file, MCIndAreasData) else "links"

    # Monte Carlo years filtering
    if not mc_ind_path.is_dir():
        return []
    all_mc_years = [d.name for d in mc_ind_path.iterdir()]
    if mc_years:
        all_mc_years = [y for y in all_mc_years if int(y) in frozenset(mc_years)]
    if not all_mc_years:
        return []

    # Links / Areas ids filtering

    # The list of areas and links is the same whatever the MC year under consideration:
    # Therefore we choose the first year by default avoiding useless scanning directory operations.
    first_mc_year = all_mc_years[0]
    areas_or_links_ids = _filter_files(mc_ind_path / first_mc_year / output_type, set(ids_to_consider))

    # Frequency and query file filtering
    folders_to_check = [mc_ind_path / first_mc_year / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop on MC years to return the whole list of files
    return [
        OutputFile(
            path=mc_ind_path / mc_year / output_type / area_or_link / file,
            year=int(mc_year),
            location=area_or_link,
        )
        for mc_year in all_mc_years
        for area_or_link, files in filtered_files.items()
        for file in files
    ]


def identify_mc_all_files(
    output_path: Path,
    query_file: MCAllAreasData | MCAllLinksData,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
) -> list[OutputFile]:
    mode_dir = find_mode_dir(output_path)
    if mode_dir is None:
        raise OutputSubFolderNotFound(output_path.name, f"economy/{MCRoot.MC_ALL.value}")
    mc_all_path = mode_dir / MCRoot.MC_ALL.value
    output_type = "areas" if isinstance(query_file, MCAllAreasData) else "links"

    # Links / Areas ids filtering
    areas_or_links_ids = _filter_files(mc_all_path / output_type, set(ids_to_consider))

    # Frequency and query file filtering
    folders_to_check = [mc_all_path / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop to return the whole list of files
    return [
        OutputFile(path=mc_all_path / output_type / area_or_link / file, year=None, location=area_or_link)
        for area_or_link, files in filtered_files.items()
        for file in files
    ]


def identify_files(
    output_path: Path,
    file_type: OutputDataType,
    frequency: MatrixFrequency,
    item_ids: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> list[OutputFile]:
    """
    Returns the list of matrix files that correspond to the filters in arguments.
    """
    match file_type:
        case MCIndAreasData() | MCIndLinksData():
            return identify_mc_ind_files(output_path, file_type, frequency, item_ids, mc_years)
        case MCAllAreasData() | MCAllLinksData():
            return identify_mc_all_files(output_path, file_type, frequency, item_ids)
        case _:
            raise MCRootNotHandled(f"Unknown output file type: {file_type}")


def is_details(query_file: OutputDataType) -> bool:
    return query_file in [
        MCIndAreasData.DETAILS,
        MCAllAreasData.DETAILS,
        MCIndAreasData.DETAILS_ST_STORAGE,
        MCAllAreasData.DETAILS_ST_STORAGE,
        MCIndAreasData.DETAILS_RES,
        MCAllAreasData.DETAILS_RES,
    ]


def is_synthesis(file_type: OutputDataType) -> bool:
    match file_type:
        case MCIndAreasData() | MCIndLinksData():
            return False
        case MCAllAreasData() | MCAllLinksData():
            return True
        case _:
            raise MCRootNotHandled(f"Unknown output file type: {file_type}")


def location_type(file_type: OutputDataType) -> Literal["area", "link"]:
    match file_type:
        case MCIndAreasData() | MCAllAreasData():
            return "area"
        case MCIndLinksData() | MCAllLinksData():
            return "link"
    raise ValueError(f"Unknown query file type: {file_type}")


@dataclass(frozen=True)
class OutputMatrix:
    """
    Carries information about the current state of a matrix which was read from an output file, and possibly already
    transformed (column fitlers, pivots, ...).
    """

    path: Path  # File from which was read
    file_type: OutputDataType
    year: int | None  # None if we're working on mc-all data
    location: str  # Area or link

    data: LazyOutputTable

    def location_col(self) -> Literal["area", "link"]:
        return location_type(self.file_type)

    def filter_false(self, predicate: Callable[[OutputColumn], bool]) -> "OutputMatrix":
        return dataclasses.replace(self, data=self.data.select(predicate))

    def sort_columns(self, sort_key: Callable[[OutputColumn], Any]) -> "OutputMatrix":
        return dataclasses.replace(self, data=self.data.sort_columns(sort_key))

    def to_polars(self, naming: Callable[[OutputColumn], str]) -> pl.DataFrame:
        return self.data.collect().to_polars(naming)


def stack_matrix(output_data: OutputMatrix) -> OutputMatrix:
    """
    Transforms "details" matrices from wide table form to narrow table form.

    Before: X columns for each cluster
    After: X columns + 1 column for the cluster id
    """
    initial_cols = output_data.data.columns
    initial_df = output_data.data.dataframe

    # Mapping cluster variable -> column index in final DF
    col_indices: dict[ClusterVarColumn, int] = {}
    cols_count = 0
    # For each cluster, we gather the mapping final col index -> initial col index
    clusters_cols_indices: dict[str, dict[int, int]] = {}

    preserved_cols_indices = []

    final_columns: list[OutputColumn] = ["cluster"]
    for idx, col in enumerate(initial_cols):
        if not isinstance(col, VarColumn):
            preserved_cols_indices.append(idx)
            final_columns.append(col)
            continue
        cluster_id = col.variable
        cluster_var = ClusterVarColumn(col.unit, col.stat)
        col_idx = col_indices.get(cluster_var, None)
        if col_idx is None:
            final_columns.append(cluster_var)
            col_idx = cols_count
            col_indices[cluster_var] = col_idx
            cols_count += 1
        cluster_indices = clusters_cols_indices.setdefault(cluster_id, {})
        cluster_indices[col_idx] = idx

    # For each cluster create the corresponding dataframe, which will be a "slice" of the final dataframe
    # Columns of each dataframe are: the index columns such as time etc, the new "cluster" column
    # and then the actual variables columns
    final_clusters_dfs = []
    preserved_cols = [cs.by_index(c) for c in preserved_cols_indices]
    for cluster, dfs in clusters_cols_indices.items():
        var_cols = [cs.by_index(dfs[c]).alias(str(c)) for c in range(0, cols_count) if c in dfs]
        cluster_columns = initial_df.select(*preserved_cols, *var_cols)
        with_cluster_id = cluster_columns.select(pl.lit(cluster).alias("cluster"), pl.all())
        final_clusters_dfs.append(with_cluster_id)

    # Then just concatenate the clusters slices together
    final_df = pl.concat(final_clusters_dfs, how="vertical_relaxed")

    final_table = LazyOutputTable(dataframe=final_df, columns=final_columns)
    return dataclasses.replace(output_data, data=final_table)


def filter_columns(data: OutputMatrix, filters: Sequence[str]) -> OutputMatrix:
    lower_case_filters = set(f.lower() for f in filters)  # TODO: only once for all matrices
    if not lower_case_filters:
        return data

    synthesis = is_synthesis(data.file_type)

    def passes_filter(col: OutputColumn) -> bool:
        # TODO:
        # This logic seems nonsense, and is not even in line with R package antaresRead.
        # Should probably be broken to get simpler ?
        match col:
            case ClusterVarColumn(variable=var):
                return any(f in var.lower() for f in lower_case_filters)
            case VarColumn(variable=var):
                if synthesis:
                    return any(f in var.lower() for f in lower_case_filters)
                else:
                    return var.lower() in lower_case_filters
            case _:
                return True

    return data.filter_false(passes_filter)


def add_index_columns(output_matrix: OutputMatrix) -> OutputMatrix:
    """
    Adds columns location, year, and time
    """
    initial_df = output_matrix.data.dataframe
    year = output_matrix.year

    location_col = output_matrix.location_col()
    new_cols: list[OutputColumn] = [location_col, "timeId"] if year is None else [location_col, "mcYear", "timeId"]
    df = initial_df.with_row_index("time", offset=1)
    exprs = [pl.lit(output_matrix.location).alias(location_col)]
    if output_matrix.year is not None:
        exprs.append(pl.lit(output_matrix.year).alias("mcYear"))
    final_df = df.select(*exprs, pl.all())
    final_table = LazyOutputTable(dataframe=final_df, columns=new_cols + list(output_matrix.data.columns))

    return dataclasses.replace(output_matrix, data=final_table)


def get_sort_key(col: OutputColumn) -> tuple[int, str | None]:
    """
    area/link - cluster - year - time - others
    """
    values: dict[OutputColumn, int] = {"area": 1, "link": 1, "cluster": 2, "mcYear": 3, "timeId": 4}
    match col:
        case VarColumn():
            return 5, None
        case ClusterVarColumn(variable=var):
            return 5, var
        case _:
            return (values.get(col, 5), None)


def sort_columns(output_matrix: OutputMatrix) -> OutputMatrix:
    return output_matrix.sort_columns(get_sort_key)


def iterate_output_matrices(
    output_path: Path,
    query_file: OutputDataType,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    columns_names: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> Iterator[OutputMatrix]:
    if not output_path.is_dir():
        raise OutputNotFound(output_path.name)

    files = identify_files(output_path, query_file, frequency, ids_to_consider, mc_years)

    logger.info(f"Iterating over {len(files)} {frequency.value} files from output {output_path.name}")

    # Ignore time related columns, only get variables
    start_col = get_start_column(frequency)

    def parse_file(f: OutputFile) -> OutputMatrix:
        output_df = parse_output_file(f.path, start_col)
        return OutputMatrix(
            f.path,
            file_type=query_file,
            year=f.year,
            location=f.location,
            data=LazyOutputTable(dataframe=output_df.dataframe.lazy(), columns=output_df.columns),
        )

    output_data = map(parse_file, files)

    output_data = map(add_index_columns, output_data)

    if is_details(query_file):
        output_data = map(stack_matrix, output_data)

    # Filter colummns
    output_data = map(lambda m: filter_columns(m, columns_names), output_data)

    # Final sort
    output_data = map(sort_columns, output_data)

    return output_data


def aggregation_column_naming(col: OutputColumn) -> str:
    match col:
        case VarColumn(variable=var, stat=stat):
            return f"{var} {stat}".upper() if stat else var  # TODO: why upper case only for mc-all ??
        case ClusterVarColumn(variable=var):
            return var
        case _:
            return col


def aggregate_output_data(
    output_path: Path,
    query_file: OutputDataType,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    columns_names: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> Iterator[pl.DataFrame]:
    matrices = iterate_output_matrices(
        output_path=output_path,
        query_file=query_file,
        frequency=frequency,
        ids_to_consider=ids_to_consider,
        columns_names=columns_names,
        mc_years=mc_years,
    )

    return map(lambda m: m.to_polars(aggregation_column_naming), matrices)


def get_output_item_table(
    output_path: Path,
    query_file: OutputDataType,
    frequency: MatrixFrequency,
    item_id: str,
    mc_year: int | None = None,
) -> OutputTable:
    """
    Returns the output table for one business item.
    # TODO SL: not in "aggregation" file
    """
    years = [mc_year] if mc_year is not None else []
    files = identify_files(output_path, query_file, frequency, [item_id], years)
    if len(files) != 1:
        raise OutputNotFound(f"Could not find output file for {item_id} in {output_path.name}")
    output_file = files[0]
    return parse_output_file(output_file.path, get_start_column(frequency))
