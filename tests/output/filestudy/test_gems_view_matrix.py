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

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl
import pytest

from antarest.core.exceptions import GemsViewMatrixNotFound, GemsViewNotFound, InvalidGemsViewData
from antarest.output.filestudy.gems_view_matrix import get_view_matrix
from antarest.output.filestudy.gems_views import extract_gems_views
from antarest.output.model.gems_views import (
    GemsAggregationPattern,
    GemsMetricLocation,
    GemsTaxonomyViews,
    GemsViewIndex,
    GemsViewLocations,
    GemsViewMatrix,
)
from antarest.study.business.model.gems.view import GemsTimeGranularity

HOUR = GemsTimeGranularity.HOUR
DAY = GemsTimeGranularity.DAY
MONTH = GemsTimeGranularity.MONTH
YEAR = GemsTimeGranularity.YEAR
JAN_1 = datetime(2026, 1, 1)
STATS = ["exp", "std", "min", "max"]

STORAGE_COLUMNS = [
    f"area3_short_term_storage_st / {metric}" for metric in ["CASHFLOW", "LEVELS", "P_INJECTION", "P_WITHDRAWAL"]
]

# Written by `_write_view`, for the cases the shared test data lacks
VIEW_FILE = "view_area--pattern--20261104T153938.parquet"
SCHEMA = {
    "metric_id": pl.String,
    "metric_location": pl.String,
    "breakdown_properties": pl.String,
    "view_date": pl.Datetime("us"),
    "scenario_id": pl.UInt32,
    "metric_value": pl.Float64,
    "scenario_stat": pl.String,
}


@pytest.fixture
def views(gems_views_output_dir: Path) -> list[GemsTaxonomyViews]:
    """
    The views of the shared test data, as materialized.
    """
    return extract_gems_views(gems_views_output_dir)


def _row(
    metric_id: str,
    value: float,
    scenario_id: int | None = 0,
    view_date: datetime | None = JAN_1,
    location: str | None = "area1_node",
    breakdown: str = "{}",
    stat: str | None = None,
) -> dict[str, Any]:
    return dict(zip(SCHEMA, [metric_id, location, breakdown, view_date, scenario_id, value, stat], strict=True))


def _stats_rows(metric_id: str, values: list[float], **kwargs: Any) -> list[dict[str, Any]]:
    return [_row(metric_id, value, None, stat=stat, **kwargs) for stat, value in zip(STATS, values, strict=True)]


def _write_view(output_path: Path, rows: list[dict[str, Any]], schema: dict[str, Any] = SCHEMA) -> Path:
    path = output_path / "views" / "output" / VIEW_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, schema=schema).write_parquet(path)
    return path


def _views(
    time_granularity: GemsTimeGranularity, scenario: bool, locations: tuple[str, ...] = ("area1_node",)
) -> list[GemsTaxonomyViews]:
    """
    `view_area` of the file of `_write_view`, as materialized.
    """
    pattern = GemsAggregationPattern(id="pattern", scenario=scenario, time_granularity=time_granularity)
    view = GemsViewLocations(
        metrics_location=[GemsMetricLocation(id=location) for location in locations], aggregation_patterns=[pattern]
    )
    return [GemsTaxonomyViews(taxonomy="balance", view_ids={"view_area": view})]


def test_year_matrix(gems_views_output_dir: Path, views: list[GemsTaxonomyViews]) -> None:
    index = GemsViewIndex(start_date=JAN_1, steps=3, time_granularity=HOUR, step_size=1)
    columns = [(name, "", "") for name in STORAGE_COLUMNS]

    year_1 = get_view_matrix(gems_views_output_dir, "my-output", views, "view_storage", HOUR, "area3_node", 1)
    assert year_1 == GemsViewMatrix(
        index=index, columns=columns, data=[[686, 5000, 0, 7], [319, 5000, 0, 8], [5, 5000, 0, 1]]
    )
    year_2 = get_view_matrix(gems_views_output_dir, "my-output", views, "view_storage", HOUR, "area3_node", 2)
    assert year_2 == GemsViewMatrix(
        index=index, columns=columns, data=[[35, 5000, 0, 7], [40, 5000, 0, 8], [5, 5000, 0, 1]]
    )
    with pytest.raises(GemsViewMatrixNotFound, match="Monte Carlo year 3 not found for location 'area3_node'"):
        get_view_matrix(gems_views_output_dir, "my-output", views, "view_storage", HOUR, "area3_node", 3)


def test_statistics_matrix(gems_views_output_dir: Path, views: list[GemsTaxonomyViews]) -> None:
    matrix = get_view_matrix(gems_views_output_dir, "my-output", views, "view_storage", YEAR, "area3_node", None)

    assert matrix == GemsViewMatrix(
        index=GemsViewIndex(start_date=JAN_1, steps=1, time_granularity=YEAR, step_size=1),
        columns=[(name, "", stat) for name in STORAGE_COLUMNS for stat in STATS],
        data=[[5145405.5, 2005321.5, 3140084, 7150727, 5000, 0, 5000, 5000, 0, 0, 0, 0, 4194, 0, 4194, 4194]],
    )


def test_column_order(gems_views_output_dir: Path, views: list[GemsTaxonomyViews]) -> None:
    # Grouped by breakdown, then sorted by metric
    thermal = get_view_matrix(gems_views_output_dir, "my-output", views, "view_thermal", HOUR, "area1_node", 1)
    metrics = ["GENERATION", "MIN_GEN", "NODU", "NP_COST", "PROFIT"]
    assert thermal.columns == [(f"area1_thermal_{name} / {m}", "", "") for name in ["gas", "nuclear"] for m in metrics]

    # Columns without breakdown first
    area = get_view_matrix(gems_views_output_dir, "my-output", views, "view_area", YEAR, "area1_node", None)
    names = list(dict.fromkeys(name for name, _, _ in area.columns))
    assert names[:2] == ["AVL_DTG", "BALANCE"]
    assert names[-2:] == ["gas / DTG_BY_TECHNOLOGY", "nuclear / DTG_BY_TECHNOLOGY"]
    # Undated here: not part of the series
    assert "H_PUMP" not in names


def test_index(tmp_path: Path) -> None:
    # Rows in any order: the matrix starts at the earliest date
    dates = [datetime(2026, 1, 3), JAN_1, datetime(2026, 1, 2)]
    _write_view(tmp_path, [_row("LOAD", d.day, view_date=d) for d in dates])

    matrix = get_view_matrix(tmp_path, "my-output", _views(DAY, False), "view_area", DAY, "area1_node", 1)

    assert matrix.index == GemsViewIndex(start_date=JAN_1, steps=3, time_granularity=DAY, step_size=1)
    assert matrix.data == [[1], [2], [3]]


@pytest.mark.parametrize(
    ("time_granularity", "dates", "step_size"),
    [
        # An hourly view of an output with a 2-hour calendar
        pytest.param(HOUR, [JAN_1 + timedelta(hours=2 * i) for i in range(3)], 2, id="hour"),
        pytest.param(MONTH, [datetime(2026, month, 1) for month in (1, 4, 7)], 3, id="month"),
    ],
)
def test_index_with_a_longer_step(
    tmp_path: Path, time_granularity: GemsTimeGranularity, dates: list[datetime], step_size: int
) -> None:
    _write_view(tmp_path, [_row("LOAD", i, view_date=d) for i, d in enumerate(dates)])
    views = _views(time_granularity, False)

    matrix = get_view_matrix(tmp_path, "my-output", views, "view_area", time_granularity, "area1_node", 1)

    assert matrix.index == GemsViewIndex(
        start_date=JAN_1, steps=3, time_granularity=time_granularity, step_size=step_size
    )
    assert matrix.data == [[0], [1], [2]]


def test_values_without_date(tmp_path: Path) -> None:
    _write_view(tmp_path, _stats_rows("H_PUMP", [0, 1, 2, 3], view_date=None))

    matrix = get_view_matrix(tmp_path, "my-output", _views(YEAR, True), "view_area", YEAR, "area1_node", None)

    assert matrix.index == GemsViewIndex(start_date=None, steps=1, time_granularity=YEAR, step_size=1)
    assert matrix.data == [[0, 1, 2, 3]]


def test_missing_values(tmp_path: Path) -> None:
    rows = _stats_rows("OV_COST", [1, 2, 3, float("nan")]) + _stats_rows(
        "LOAD", [5, 6, 7, 8], view_date=JAN_1 + timedelta(days=1)
    )
    _write_view(tmp_path, rows)

    matrix = get_view_matrix(tmp_path, "my-output", _views(DAY, True), "view_area", DAY, "area1_node", None)

    # Missing cells and NaN are null
    assert matrix.data == [[None] * 4 + [1, 2, 3, None], [5, 6, 7, 8] + [None] * 4]


def test_breakdown_with_several_properties(tmp_path: Path) -> None:
    # Property values are free strings
    breakdown = "{(technology,battery (li-ion)),(company,A, B)}"
    _write_view(tmp_path, _stats_rows("DTG", [1, 2, 3, 4], breakdown=breakdown))

    matrix = get_view_matrix(tmp_path, "my-output", _views(YEAR, True), "view_area", YEAR, "area1_node", None)

    assert matrix.columns == [("battery (li-ion) / A, B / DTG", "", stat) for stat in STATS]


def test_output_path_with_glob_characters(
    gems_views_output_dir: Path, tmp_path: Path, views: list[GemsTaxonomyViews]
) -> None:
    # `[v2]` is a glob pattern (`*` and `?` are invalid on Windows)
    output_path = tmp_path / "Study [v2]" / "output" / gems_views_output_dir.name
    shutil.copytree(gems_views_output_dir, output_path)

    expected = get_view_matrix(gems_views_output_dir, "my-output", views, "view_storage", YEAR, "area3_node", None)
    assert get_view_matrix(output_path, "my-output", views, "view_storage", YEAR, "area3_node", None) == expected


def test_matrix_not_found(gems_views_output_dir: Path, tmp_path: Path, views: list[GemsTaxonomyViews]) -> None:
    output = gems_views_output_dir
    with pytest.raises(GemsViewNotFound, match="View 'view_other' not found in output 'my-output'"):
        get_view_matrix(output, "my-output", views, "view_other", YEAR, "area3_node", None)
    # Ids are exact matches, not patterns
    with pytest.raises(GemsViewNotFound):
        get_view_matrix(output, "my-output", views, "view_*", YEAR, "area3_node", None)
    # No Monte Carlo year: the `scenario: true` pattern
    with pytest.raises(
        GemsViewMatrixNotFound, match="time granularity 'hour' and scenario 'true' not found in view 'view_storage'"
    ):
        get_view_matrix(output, "my-output", views, "view_storage", HOUR, "area3_node", None)
    # A Monte Carlo year: the `scenario: false` pattern
    with pytest.raises(GemsViewMatrixNotFound, match="time granularity 'year' and scenario 'false'"):
        get_view_matrix(output, "my-output", views, "view_storage", YEAR, "area3_node", 1)

    # Only `area3_node` has a storage, checked before the file lookup (this output has no file)
    with pytest.raises(GemsViewMatrixNotFound, match="Location 'area1_node' not found in view 'view_storage'"):
        get_view_matrix(tmp_path, "my-output", views, "view_storage", YEAR, "area1_node", None)
    with pytest.raises(GemsViewMatrixNotFound, match="No file for the aggregation pattern 'annual_all_scenario'"):
        get_view_matrix(tmp_path, "my-output", views, "view_storage", YEAR, "area3_node", None)


@pytest.mark.parametrize(
    ("time_granularity", "scenario", "mc_year", "rows"),
    [
        pytest.param(YEAR, True, None, _stats_rows("LOAD", [1, 2, 3, 4]), id="statistics"),
        pytest.param(HOUR, False, 1, [_row("LOAD", 1)], id="year"),
    ],
)
def test_location_left_out_of_the_pattern(
    tmp_path: Path,
    time_granularity: GemsTimeGranularity,
    scenario: bool,
    mc_year: int | None,
    rows: list[dict[str, Any]],
) -> None:
    # Left out of the pattern by a `location-filter`: an empty matrix, not an error
    _write_view(tmp_path, rows)
    views = _views(time_granularity, scenario, locations=("area1_node", "area2_node"))

    matrix = get_view_matrix(tmp_path, "my-output", views, "view_area", time_granularity, "area2_node", mc_year)

    index = GemsViewIndex(start_date=None, steps=0, time_granularity=time_granularity, step_size=1)
    assert matrix == GemsViewMatrix(index=index, columns=[], data=[])


def test_invalid_view_files(tmp_path: Path) -> None:
    rows = _stats_rows("LOAD", [1, 2, 3, 4])
    views = _views(YEAR, True)

    # Duplicates make the pivot fail instead of keeping one value
    _write_view(tmp_path, rows + rows[:1])
    with pytest.raises(pl.exceptions.PolarsError):
        get_view_matrix(tmp_path, "my-output", views, "view_area", YEAR, "area1_node", None)

    schema = {name: dtype for name, dtype in SCHEMA.items() if name != "metric_value"}
    _write_view(tmp_path, [{name: row[name] for name in schema} for row in rows], schema=schema)
    with pytest.raises(InvalidGemsViewData, match=f"'{VIEW_FILE}': the file is not a valid view file"):
        get_view_matrix(tmp_path, "my-output", views, "view_area", YEAR, "area1_node", None)

    _write_view(tmp_path, rows).write_bytes(b"not a parquet file")
    with pytest.raises(InvalidGemsViewData, match="the file is not a valid view file") as ctx:
        get_view_matrix(tmp_path, "my-output", views, "view_area", YEAR, "area1_node", None)
    assert ctx.value.status_code == 500
    assert str(tmp_path) not in ctx.value.detail
