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

from pathlib import Path

from antarest.output.model import (
    MatrixAggregationResultDTO,
    StudyDownloadDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.output.storage.v2.iteration import iterate_areas_df
from antarest.output.storage.v2.metadata import IParquetOutputMetadata


def build_matrix_aggregation_result(
    output_metadata: IParquetOutputMetadata, parquet_dir: Path, data_selection: StudyDownloadDTO
) -> MatrixAggregationResultDTO:

    element_results: dict[str, TimeSeriesData] = {}  # one TimeSeriesData for each element of the system

    if data_selection.type in {StudyDownloadType.AREA, StudyDownloadType.DISTRICT}:
        area_dfs = iterate_areas_df(
            output_metadata,
            parquet_dir,
            data_selection.level,
            data_selection.years,
            data_selection.filter,
            data_selection.columns,
        )
        for area_df in area_dfs:
            year, area_id, df, vars = area_df.year, area_df.area_id, area_df.data, area_df.variables
            ts_data = element_results.setdefault(
                area_id, TimeSeriesData(type=data_selection.type, name=area_id, data={})
            )
            for var_index, var in enumerate(vars):
                numerical_data = df.to_series(var_index).cast(float).to_list()
                ts_data.data.setdefault(str(year), []).append(
                    TimeSerie(name=var.name, unit=var.unit_repr(), data=numerical_data)
                )

    return MatrixAggregationResultDTO(
        index=output_metadata.get_time_index(data_selection.level),
        data=list(element_results.values()),
    )
