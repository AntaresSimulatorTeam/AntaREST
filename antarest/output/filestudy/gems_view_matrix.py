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
Reading of one location of a GEMS view as a matrix (file layout in `gems_view_files`).
"""

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from antarest.core.exceptions import GemsViewMatrixNotFound, GemsViewNotFound, InvalidGemsViewData
from antarest.output.filestudy.gems_view_files import (
    BREAKDOWN_PROPERTIES_COL,
    METRIC_ID_COL,
    METRIC_LOCATION_COL,
    METRIC_VALUE_COL,
    SCENARIO_ID_COL,
    SCENARIO_STAT_COL,
    VIEW_DATE_COL,
    list_view_files,
)
from antarest.output.model.gems_views import (
    GemsTaxonomyViews,
    GemsViewColumn,
    GemsViewIndex,
    GemsViewMatrix,
)
from antarest.study.business.model.gems.view import GemsTimeGranularity

_VIEW_FILE_SCHEMA = pl.Schema(
    {
        METRIC_ID_COL: pl.String(),
        METRIC_LOCATION_COL: pl.String(),
        BREAKDOWN_PROPERTIES_COL: pl.String(),
        VIEW_DATE_COL: pl.Datetime("us"),
        SCENARIO_ID_COL: pl.Int64(),
        METRIC_VALUE_COL: pl.Float64(),
        SCENARIO_STAT_COL: pl.String(),
    }
)

_DURATIONS = {
    GemsTimeGranularity.HOUR: timedelta(hours=1),
    GemsTimeGranularity.DAY: timedelta(days=1),
    GemsTimeGranularity.WEEK: timedelta(weeks=1),
}


def get_view_matrix(
    output_dir: Path,
    output_id: str,
    views: list[GemsTaxonomyViews],
    view_id: str,
    time_granularity: GemsTimeGranularity,
    metric_location: str,
    mc_year: int | None,
) -> GemsViewMatrix:
    """
    Returns one location of a view as a matrix: the values of the 1-based `mc_year` (pattern with `scenario: false`),
    or without it the statistics across years (`scenario: true`). The pattern is looked up in `views`, the
    materialized views. A location left out of the pattern by a `location-filter` gives an empty matrix.

    Raises:
        GemsViewNotFound: if there is no view with this id.
        GemsViewMatrixNotFound: if there is no such pattern, location, file or Monte Carlo year.
        InvalidGemsViewData: if the view file is invalid.
    """
    scenario = mc_year is None
    view_file = _find_view_file(output_dir, output_id, views, view_id, time_granularity, scenario, metric_location)
    return _read_view_matrix(view_file, time_granularity, metric_location, mc_year)


def _find_view_file(
    output_dir: Path,
    output_id: str,
    views: list[GemsTaxonomyViews],
    view_id: str,
    time_granularity: GemsTimeGranularity,
    scenario: bool,
    metric_location: str,
) -> Path:
    view = next((taxonomy.view_ids[view_id] for taxonomy in views if view_id in taxonomy.view_ids), None)
    if view is None:
        raise GemsViewNotFound(output_id, view_id)
    # The GEMS spec allows one pattern per (time granularity, scenario)
    patterns = (
        p for p in view.aggregation_patterns if (p.time_granularity, p.scenario) == (time_granularity, scenario)
    )
    aggregation = next(patterns, None)
    if aggregation is None:
        raise GemsViewMatrixNotFound(
            f"Aggregation pattern with time granularity '{time_granularity}' and scenario '{str(scenario).lower()}'"
            f" not found in view '{view_id}'"
        )
    if all(location.id != metric_location for location in view.metrics_location):
        raise GemsViewMatrixNotFound(f"Location '{metric_location}' not found in view '{view_id}'")

    files = list_view_files(output_dir, view_id, aggregation.id)
    if not files:
        raise GemsViewMatrixNotFound(
            f"No file for the aggregation pattern '{aggregation.id}' of view '{view_id}' in output '{output_id}'"
        )
    return files[-1]


def _read_view_matrix(
    view_file: Path, time_granularity: GemsTimeGranularity, metric_location: str, mc_year: int | None
) -> GemsViewMatrix:
    location = pl.col(METRIC_LOCATION_COL) == metric_location
    year = pl.lit(True) if mc_year is None else pl.col(SCENARIO_ID_COL) == mc_year - 1
    rows = _read_rows(view_file, location & year)
    if rows.is_empty():
        if mc_year is not None and not _read_rows(view_file, location, limit=1).is_empty():
            raise GemsViewMatrixNotFound(f"Monte Carlo year {mc_year} not found for location '{metric_location}'")
        # Left out by a `location-filter`: no values, not an error
        index = GemsViewIndex(start_date=None, steps=0, time_granularity=time_granularity, step_size=1)
        return GemsViewMatrix(index=index, columns=[], data=[])
    return _build_matrix(time_granularity, rows)


def _read_rows(path: Path, predicate: pl.Expr, limit: int | None = None) -> pl.DataFrame:
    try:
        return (
            pl.scan_parquet(
                path,
                glob=False,
                schema=_VIEW_FILE_SCHEMA,
                extra_columns="ignore",
                # `scenario_id` is UInt32 when built from Parquet tables, Int64 from CSV tables and in statistics
                cast_options=pl.ScanCastOptions(integer_cast="upcast"),
            )
            .filter(predicate)
            .slice(0, limit)
            .collect()
        )
    except (pl.exceptions.PolarsError, OSError) as e:
        raise InvalidGemsViewData(path.name, "the file is not a valid view file") from e


def _build_matrix(granularity: GemsTimeGranularity, rows: pl.DataFrame) -> GemsViewMatrix:
    """
    Pivots the rows to one row per date and one column per metric, breakdown and stat.
    """
    dates = rows[VIEW_DATE_COL].drop_nulls().unique().sort()
    if not dates.is_empty():
        # Undated values (time-independent variables) are not part of the series
        rows = rows.filter(pl.col(VIEW_DATE_COL).is_not_null())

    column_keys = [METRIC_ID_COL, BREAKDOWN_PROPERTIES_COL, SCENARIO_STAT_COL]
    stat_order = pl.col(SCENARIO_STAT_COL).replace_strict({"exp": 0, "std": 1, "min": 2, "max": 3}, default=0)
    has_breakdown = pl.col(BREAKDOWN_PROPERTIES_COL) != "{}"
    columns = rows.select(column_keys).unique().sort(has_breakdown, BREAKDOWN_PROPERTIES_COL, METRIC_ID_COL, stat_order)
    # Pivoted on positions: a column key is not a column name
    matrix = (
        rows.join(columns.with_row_index("position"), on=column_keys, nulls_equal=True)
        .pivot(on="position", index=VIEW_DATE_COL, values=METRIC_VALUE_COL)
        .sort(VIEW_DATE_COL)
        .select(pl.col(str(i)).fill_nan(None) for i in range(columns.height))
    )
    return GemsViewMatrix(
        index=_build_index(granularity, dates),
        columns=[_column(metric_id, breakdown, stat) for metric_id, breakdown, stat in columns.rows()],
        data=[list(row) for row in matrix.rows()],
    )


def _build_index(granularity: GemsTimeGranularity, dates: pl.Series) -> GemsViewIndex:
    if dates.is_empty():
        return GemsViewIndex(start_date=None, steps=1, time_granularity=granularity, step_size=1)
    start = dates[0]
    # From the first two dates only: a gap would shift the next labels
    step_size = _count_periods(granularity, start, dates[1]) if len(dates) > 1 else 1
    return GemsViewIndex(start_date=start, steps=len(dates), time_granularity=granularity, step_size=step_size)


def _count_periods(granularity: GemsTimeGranularity, start: datetime, end: datetime) -> int:
    """
    Returns the number of whole periods of the granularity from `start` to `end`.
    """
    if granularity == GemsTimeGranularity.YEAR:
        return end.year - start.year
    if granularity == GemsTimeGranularity.MONTH:
        return (end.year - start.year) * 12 + end.month - start.month
    return (end - start) // _DURATIONS[granularity]


def _column(metric_id: str, breakdown: str, stat: str | None) -> GemsViewColumn:
    # Free-string values: `{(technology,battery (li-ion)),(company,A)}`
    pairs = [] if breakdown == "{}" else breakdown.removeprefix("{(").removesuffix(")}").split("),(")
    return " / ".join([*(pair.partition(",")[2] for pair in pairs), metric_id]), "", stat or ""
