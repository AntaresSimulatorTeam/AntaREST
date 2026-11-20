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
Reading of a GEMS view of an output directory as a matrix, from the file of one aggregation pattern:

    <output>/views/output/<view_id>--<aggregation_id>--<timestamp>.parquet
"""

import logging
import re
from pathlib import Path

import polars as pl

from antarest.core.exceptions import (
    GemsViewMatrixNotFound,
    GemsViewNotFound,
    InvalidGemsViewData,
    InvalidGemsViewMatrixRequest,
)
from antarest.output.filestudy.gems_views import parse_gems_view_configs
from antarest.output.model.gems_views import GemsViewColumn, GemsViewIndex, GemsViewMatrix
from antarest.output.model.output_type import GEMS_VIEWS_DIR
from antarest.study.business.model.gems.view import GemsTimeGranularity

logger = logging.getLogger(__name__)

_VIEW_FILE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.String(),
        "metric_location": pl.String(),
        "breakdown_properties": pl.String(),
        "view_date": pl.Datetime("us"),
        "scenario_id": pl.Int64(),
        "metric_value": pl.Float64(),
        "scenario_stat": pl.String(),
    }
)
# `(technology,nuclear)` in a breakdown such as `{(technology,nuclear),(company,A)}`
_BREAKDOWN_PAIR_REGEX = re.compile(r"\([^(),]*,([^()]*)\)")


def get_view_matrix(
    output_dir: Path,
    output_id: str,
    view_id: str,
    aggregation_id: str,
    metric_location: str,
    mc_year: int | None,
) -> GemsViewMatrix:
    """
    Returns one location of an aggregation pattern of a view as a matrix,
    for the 1-based Monte Carlo year `mc_year` if the pattern has one set of values per year.

    Raises:
        GemsViewNotFound: if the output has no config for this view.
        GemsViewMatrixNotFound: if there is no data for this aggregation pattern, location or Monte Carlo year.
        InvalidGemsViewMatrixRequest: if `mc_year` is missing or not allowed for this aggregation pattern.
        InvalidGemsViewData: if the view file cannot be read or contradicts the view file contract.
    """
    view_config = next((config for config in parse_gems_view_configs(output_dir) if config.id == view_id), None)
    if view_config is None:
        raise GemsViewNotFound(output_id, view_id)
    aggregation = next((a for a in view_config.aggregations_patterns if a.id == aggregation_id), None)
    if aggregation is None:
        raise GemsViewMatrixNotFound(f"Aggregation pattern '{aggregation_id}' not found in view '{view_id}'")

    pattern = f"aggregation pattern '{aggregation_id}' of view '{view_id}'"
    if aggregation.scenario and mc_year is not None:
        raise InvalidGemsViewMatrixRequest(
            f"The {pattern} holds statistics across Monte Carlo years: no Monte Carlo year can be selected"
        )
    if not aggregation.scenario and mc_year is None:
        raise InvalidGemsViewMatrixRequest(
            f"The {pattern} holds one set of values per Monte Carlo year: a Monte Carlo year is required"
        )

    # Matched from a directory listing: the ids are never joined into a path
    prefix = f"{view_config.id}--{aggregation.id}--"
    files = (output_dir / GEMS_VIEWS_DIR / "output").glob("*.parquet")
    path = max((file for file in files if file.name.startswith(prefix)), default=None)
    if path is None:
        raise GemsViewMatrixNotFound(f"No file for the {pattern} in output '{output_id}'")

    location = pl.col("metric_location") == metric_location
    year = pl.lit(True) if mc_year is None else pl.col("scenario_id") == mc_year - 1
    rows = _read_rows(path, location & year)
    if rows.is_empty():
        # Second scan on errors only: tells a missing location from a missing year
        if mc_year is not None and not _read_rows(path, location, limit=1).is_empty():
            raise GemsViewMatrixNotFound(
                f"Monte Carlo year {mc_year} not found for location '{metric_location}' in the {pattern}"
            )
        raise GemsViewMatrixNotFound(f"Location '{metric_location}' not found in the {pattern}")
    return _build_matrix(aggregation.time_granularity, rows)


def _read_rows(path: Path, predicate: pl.Expr, limit: int | None = None) -> pl.DataFrame:
    try:
        return (
            pl.scan_parquet(
                path,
                glob=False,
                schema=_VIEW_FILE_SCHEMA,
                extra_columns="ignore",
                # The view files we read contain different types depending on how they were built:
                # - Per-year files built from the Simulator's Parquet tables: UInt32.
                # - Per-year files built from a CSV table, like our sample test data: Int64.
                # - Statistics files: always Int64, because the builder writes pl.lit(None, dtype=pl.Int64).
                cast_options=pl.ScanCastOptions(integer_cast="upcast"),
            )
            .filter(predicate)
            .slice(0, limit)
            .collect()
        )
    except (pl.exceptions.PolarsError, OSError) as e:
        logger.error(f"Cannot read GEMS view file '{path}'", exc_info=e)
        raise InvalidGemsViewData(path.name, "the file is not a valid view file") from e


def _build_matrix(granularity: GemsTimeGranularity, rows: pl.DataFrame) -> GemsViewMatrix:
    """
    Pivots the rows to one row per date and one column per metric, breakdown and stat.
    """
    dates = rows["view_date"].drop_nulls().unique().sort()
    if not dates.is_empty():
        # Values without date (time-independent variables) are not part of a time series
        rows = rows.filter(pl.col("view_date").is_not_null())

    column_keys = ["metric_id", "breakdown_properties", "scenario_stat"]
    stat_order = pl.col("scenario_stat").replace_strict({"exp": 0, "std": 1, "min": 2, "max": 3}, default=0)
    has_breakdown = pl.col("breakdown_properties") != "{}"
    columns = rows.select(column_keys).unique().sort(has_breakdown, "breakdown_properties", "metric_id", stat_order)
    # Pivoted on the column positions: a column key is not a column name
    matrix = (
        # Per-year files have a null stat, which must match too
        rows.join(columns.with_row_index("position"), on=column_keys, nulls_equal=True)
        .pivot(on="position", index="view_date", values="metric_value")
        .sort("view_date")
        # Missing cells are null: a NaN from the file is missing too
        .select(pl.col(str(i)).fill_nan(None) for i in range(columns.height))
    )
    return GemsViewMatrix(
        index=_build_index(granularity, dates),
        columns=[_column(metric_id, breakdown, stat) for metric_id, breakdown, stat in columns.rows()],
        data=[list(row) for row in matrix.rows()],
    )


def _build_index(granularity: GemsTimeGranularity, dates: pl.Series) -> GemsViewIndex:
    if dates.is_empty():
        return GemsViewIndex(start_date=None, steps=1, time_granularity=granularity)
    return GemsViewIndex(start_date=dates[0], steps=len(dates), time_granularity=granularity)


def _column(metric_id: str, breakdown: str, stat: str | None) -> GemsViewColumn:
    return " / ".join([*_BREAKDOWN_PAIR_REGEX.findall(breakdown), metric_id]), "", stat or ""
