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
"""Implement the imagrid download contract using relational metadata and parquet."""

from pathlib import Path

from antarest.output.model import (
    MatrixAggregationResultDTO,
    StudyDownloadDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.output.storage.v2.dbmodel import ElementType
from antarest.output.storage.v2.iteration import iterate_element_dfs
from antarest.output.storage.v2.layout import CLUSTER_TYPES
from antarest.output.storage.v2.metadata import IParquetOutputMetadata


def build_matrix_aggregation_result(
    output_metadata: IParquetOutputMetadata, parquet_dir: Path, data_selection: StudyDownloadDTO
) -> MatrixAggregationResultDTO:
    kinds: list[ElementType] = ["link"] if data_selection.type == StudyDownloadType.LINK else ["area"]
    if data_selection.include_clusters:
        kinds.extend(CLUSTER_TYPES)
    results: dict[str, TimeSeriesData] = {}
    for kind in kinds:
        # Restore original details-column order, even when metrics from different
        # clusters were interleaved in the simulator file.
        series: dict[tuple[int, str], list[tuple[int, TimeSerie]]] = {}
        for item in iterate_element_dfs(
            output_metadata,
            parquet_dir,
            "mc-ind",
            kind,
            data_selection.level,
            data_selection.years,
            data_selection.filter,
            data_selection.columns,
        ):
            element = item.element
            entries = series.setdefault((element.year, element.element_id), [])
            for i, (variable, position) in enumerate(zip(item.variables, item.positions)):
                entries.append(
                    (
                        position,
                        TimeSerie(
                            name=element.cluster_id or variable.name,
                            unit=variable.unit_repr(),
                            data=item.data.to_series(i).cast(float).to_list(),
                        ),
                    )
                )
        for (year, element_id), entries in series.items():
            name = "^".join(element_id.split(" - ")) if kind == "link" else element_id
            result = results.setdefault(name, TimeSeriesData(type=data_selection.type, name=name, data={}))
            result.data.setdefault(str(year), []).extend(value for _, value in sorted(entries, key=lambda p: p[0]))
    return MatrixAggregationResultDTO(
        index=output_metadata.get_time_index(data_selection.level), data=list(results.values())
    )
