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
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from polars import DataFrame, col, scan_parquet
from polars.selectors import by_index

from antarest.output.filestudy.model import VariableDescription
from antarest.output.storage.v2.dbmodel import ElementType
from antarest.output.storage.v2.metadata import IParquetOutputMetadata
from antarest.study.model import MatrixFrequency


def _parquet_file_name(element_type: ElementType, frequency: MatrixFrequency) -> str:
    match element_type:
        case "area":
            return f"mc-ind_areas_{frequency.value}.parquet"
        case _:
            raise NotImplementedError("Not yet implemented")


def _parquet_file(parquet_dir: Path, element_type: ElementType, frequency: MatrixFrequency) -> Path:
    return parquet_dir / _parquet_file_name(element_type, frequency)


@dataclass(frozen=True)
class AreaDataFrame:
    year: int
    area_id: str
    variables: Sequence[VariableDescription]
    data: DataFrame


# TODO: should go somewhere else
MC_IND_AREA_INDEX = ("mcYear", "area", "timeId")
MC_IND_AREA_COL_OFFSET = len(MC_IND_AREA_INDEX)


def iterate_areas_df(
    output_metadata: IParquetOutputMetadata,
    parquet_dir: Path,
    frequency: MatrixFrequency,
    years: Sequence[int],
    areas: Sequence[str],
    columns: Sequence[str],
) -> Iterable[AreaDataFrame]:
    """
    Yields dataframes for the selected years and areas, in sorted order, years moving last.

    Note that each area may have different variables and hence different dataframe shapes.
    For example, if 2 areas have different thermal cluster groups, that will be the case.

    Implementation first scans the parquet file for the selected rows and columns,
    then iterate on each couple year/area to yield the corresponding dataframe.
    We take care of selecting, for each area, only the variables of that area.

    Note on performance:
    we scan from the parquet file for each area, which is likely sub-optimal.
    Implementation may be tuned if considered useful later, for example by collecting a DataFrame
    with all necessary data first (but that can cause out of memory errors).
    """
    all_area_vars = output_metadata.get_variables("mc-ind", "area")
    parquet_file = _parquet_file(parquet_dir, "area", frequency)

    # Using polars lazy frame API to define the query into the underlying parquet file
    areas_df = scan_parquet(parquet_file)
    if years:
        areas_df = areas_df.filter(col("mcYear").is_in(years))
    if areas:
        areas_df = areas_df.filter(col("area").is_in(areas))

    selected_cols: set[int] = set()
    if columns:
        selected_cols = {c for c, v in enumerate(all_area_vars) if v.name in columns}

    actual_areas = output_metadata.mc_ind_areas
    if areas:
        actual_areas = [a for a in actual_areas if a.area_id in areas]
    actual_areas = sorted(actual_areas, key=lambda a: a.area_id)
    actual_years = years if years else output_metadata.mc_years
    actual_years = sorted(actual_years)

    area_vars = {a.area_id: a for a in output_metadata.mc_ind_areas}
    for year, area in itertools.product(actual_years, actual_areas):
        vars_indices = area_vars[area.area_id].variables
        if selected_cols:
            vars_indices = [v for v in vars_indices if v in selected_cols]
        df = (
            areas_df.filter(col("area") == area.area_id)
            .filter(col("mcYear") == year)
            .select(by_index([MC_IND_AREA_COL_OFFSET + v for v in vars_indices]))
            .collect()
        )

        vars = [all_area_vars[i] for i in vars_indices]
        yield AreaDataFrame(year=year, area_id=area.area_id, variables=vars, data=df)
