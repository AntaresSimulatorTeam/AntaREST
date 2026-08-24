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
Support for the "download" API
"""

import itertools
from pathlib import Path

from polars import col, scan_parquet
from polars.selectors import by_index

from antarest.output.model import (
    MatrixAggregationResultDTO,
    StudyDownloadDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.output.storage.v2.dbmodel import (
    ElementType,
)
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


def build_matrix_aggregation_result(
    output_metadata: IParquetOutputMetadata, parquet_dir: Path, data_selection: StudyDownloadDTO
) -> MatrixAggregationResultDTO:
    # TODO: works more or less but it's not quite clear.

    area_vars = output_metadata.get_variables("mc-ind", "area")

    element_results: dict[str, TimeSeriesData] = {}  # one TimeSeriesData for each element of the system

    mc_years = output_metadata.mc_years
    if data_selection.years:
        mc_years = sorted(set(mc_years).intersection(data_selection.years))

    if data_selection.type == StudyDownloadType.AREA:
        parquet_file = _parquet_file(parquet_dir, "area", data_selection.level)
        areas_df = scan_parquet(parquet_file)
        offset = 3  # 3 index column. TODO: make it less fragile by storing it somewhere? or at least have a function
        if data_selection.years:
            areas_df = areas_df.filter(col("mcYear").is_in(data_selection.years))
        if data_selection.filter:
            areas_df = areas_df.filter(col("area").is_in(data_selection.filter))
        if data_selection.columns:
            selected_cols = [offset + c for c, v in enumerate(area_vars) if v.name in data_selection.columns]
            areas_df = areas_df.select(by_index(selected_cols))

        areas = output_metadata.mc_ind_areas

        if data_selection.filter:
            areas = [a for a in areas if a.area_id in data_selection.filter]

        areas = sorted(areas, key=lambda a: a.area_id)

        for year, area in itertools.product(mc_years, areas):
            df = areas_df.filter(col("area") == area.area_id).filter(col("mcYear") == year).collect()
            ts_data = element_results.setdefault(
                area.area_id, TimeSeriesData(type=data_selection.type, name=area.area_id, data={})
            )
            for var_index in area.variables:
                var = area_vars[var_index]
                numerical_data = df.to_series(offset + var_index).cast(float).to_list()
                ts_data.data.setdefault(str(year), []).append(
                    TimeSerie(name=var.name, unit=var.unit_repr(), data=numerical_data)
                )

    return MatrixAggregationResultDTO(
        index=output_metadata.get_time_index(data_selection.level),
        data=list(element_results.values()),
    )
