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

from polars import col, read_parquet, scan_parquet
from polars.selectors import by_index
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.output.filestudy.model import MCAllAreasQueryFile, MCIndAreasQueryFile, QueryFileType
from antarest.output.model import MatrixAggregationResultDTO, StudyDownloadDTO, StudyDownloadType, TimeSeriesData
from antarest.output.storage.v2.dbmodel import DbParquetArea, DbParquetOutput, ElementType, ScenarioAggregation
from antarest.output.storage.v2.variables_fetching import get_variables_index
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
    session: Session, output_id: int, parquet_dir: Path, data_selection: StudyDownloadDTO
) -> MatrixAggregationResultDTO:
    var_index = get_variables_index(session, output_id)

    element_results: dict[str, TimeSeriesData] = {}  # one TimeSeriesData for each element of the system

    db_output = session.execute(select(DbParquetOutput).where(DbParquetOutput.id == output_id)).scalar_one()
    mc_years = db_output.playlist
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
            area_vars = var_index.get_variables("mc-ind", "area")
            selected_cols = [offset + c for c, v in enumerate(area_vars) if v.name in data_selection.columns]
            areas_df = areas_df.select(by_index(selected_cols))

        areas = session.execute(select(DbParquetArea).where(DbParquetArea.output_id == output_id)).scalars().fetchall()

        if data_selection.filter:
            areas = [a for a in areas if a in data_selection.filter]

        areas = sorted(areas, key=lambda a: a.area_id)

        for a in itertools.product(areas, data_selection):
            df = areas_df.filter(col("area") == a.area_id)
            ts_data = element_results.setdefault(
                a.area_id, TimeSeriesData(type=data_selection.type, name=a.area_id, data={})
            )
            numerical_data = df.to_series(var_index).cast(float).to_list()
            ts_data.data.setdefault(str(year), []).append(
                TimeSerie(name=var.name, unit=var.unit_repr(), data=numerical_data)
            )

    # Reshaping to target model
    element_results: dict[str, TimeSeriesData] = {}  # one TimeSeriesData for each element of the system
    for file_data in output_data:
        element_name = file_data.file.metadata.element_id
        year = file_data.file.metadata.year
        df = file_data.data.data

        # TODO: better handling of the link case, with 2 separate strings instead of that arbitrary formatting
        if data_selection.type == StudyDownloadType.LINK:
            element_name = "^".join(element_name.split(" - "))

        for var_index, var in enumerate(file_data.data.headers):
            if data_selection.columns and var.name not in data_selection.columns:
                continue
            ts_data = element_results.setdefault(
                element_name, TimeSeriesData(type=data_selection.type, name=element_name, data={})
            )
            numerical_data = df.to_series(var_index).cast(float).to_list()
            ts_data.data.setdefault(str(year), []).append(
                TimeSerie(name=var.name, unit=var.unit_repr(), data=numerical_data)
            )

    time_index = get_start_date(None, output_path, data_selection.level)
    return MatrixAggregationResultDTO(
        index=time_index,
        data=list(element_results.values()),
    )

    return MatrixAggregationResultDTO()
