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
Methods use to build the deprecated "download" models.
"""

import itertools
from pathlib import Path
from typing import Iterable

from antarest.output.filestudy.iteration import OutputFileData, iterate_output_data
from antarest.output.filestudy.model import MCIndAreasQueryFile, MCIndLinksQueryFile, QueryFileType
from antarest.output.model import (
    MatrixAggregationResultDTO,
    StudyDownloadDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.study.storage.utils import get_start_date


def build_matrix_aggregation_result(output_path: Path, data_selection: StudyDownloadDTO) -> MatrixAggregationResultDTO:
    """
    Build a MatrixAggregationResultDTO from the given output path and data.
    """
    # areas and districts are handled identically
    is_area = data_selection.type in {StudyDownloadType.AREA, StudyDownloadType.DISTRICT}

    # Gathering all relevant files data
    def get_output_data(type: QueryFileType) -> Iterable[OutputFileData]:
        return iterate_output_data(
            output_path,
            file_type=type,
            frequency=data_selection.level,
            element_ids=data_selection.filter,
            mc_years=data_selection.years,
        )

    output_data = get_output_data(MCIndAreasQueryFile.VALUES if is_area else MCIndLinksQueryFile.VALUES)

    if is_area and data_selection.include_clusters:
        output_data = itertools.chain(
            output_data,
            get_output_data(MCIndAreasQueryFile.DETAILS),
            get_output_data(MCIndAreasQueryFile.DETAILS_RES),
            get_output_data(MCIndAreasQueryFile.DETAILS_ST_STORAGE),
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
