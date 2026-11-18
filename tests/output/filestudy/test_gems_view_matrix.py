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

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

from antarest.core.exceptions import (
    GemsViewMatrixNotFound,
    GemsViewNotFound,
    InvalidGemsViewData,
    InvalidGemsViewMatrixRequest,
)
from antarest.output.filestudy.gems_view_matrix import get_view_matrix
from antarest.output.model.gems_views import GemsViewIndex, GemsViewMatrix
from antarest.study.business.model.gems.view import GemsTimeGranularity

HOUR = GemsTimeGranularity.HOUR
DAY = GemsTimeGranularity.DAY
YEAR = GemsTimeGranularity.YEAR
JAN_1 = datetime(2026, 1, 1)
STATS = ["exp", "std", "min", "max"]
VIEW_FILE = "view_area--pattern--20261104T153938.parquet"
SCHEMA = {
    "metric_id": pl.String,
    "metric_location": pl.String,
    "breakdown_properties": pl.String,
    "view_date": pl.Datetime("us"),
    # As built from a Parquet simulation table. The Int64 of a CSV one is in the builder files of the integration test.
    "scenario_id": pl.UInt32,
    "metric_value": pl.Float64,
    "scenario_stat": pl.String,
}


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


def _write_config(output_path: Path, patterns: list[tuple[str, GemsTimeGranularity, bool]]) -> None:
    """
    Writes the config of the view `view_area`, with its aggregation patterns as `(id, time granularity, scenario)`.
    """
    config = {
        "id": "view_area",
        "scope": {"location": {"taxonomy-category": "balance"}},
        "aggregations-patterns": [
            {"id": pattern_id, "time-granularity": str(granularity), "scenario": scenario}
            for pattern_id, granularity, scenario in patterns
        ],
    }
    input_dir = output_path / "views" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "view_config_view_area.yml").write_text(yaml.safe_dump({"view": config}))


def _write_file(output_path: Path, name: str, rows: list[dict[str, Any]], schema: dict[str, Any] = SCHEMA) -> Path:
    path = output_path / "views" / "output" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, schema=schema).write_parquet(path)
    return path


def _write_view(
    output_path: Path,
    rows: list[dict[str, Any]],
    granularity: GemsTimeGranularity = YEAR,
    scenario: bool = True,
    schema: dict[str, Any] = SCHEMA,
) -> Path:
    _write_config(output_path, [("pattern", granularity, scenario)])
    return _write_file(output_path, VIEW_FILE, rows, schema)


def _matrix(
    output_path: Path,
    mc_year: int | None = None,
    location: str = "area1_node",
    view_id: str = "view_area",
    aggregation_id: str = "pattern",
) -> GemsViewMatrix:
    return get_view_matrix(output_path, "my-output", view_id, aggregation_id, location, mc_year)


def test_statistics_matrix(tmp_path: Path) -> None:
    rows = (
        _stats_rows("OV_COST", [1, 2, 3, 4])
        + _stats_rows("DTG", [5, 6, 7, 8], breakdown="{(technology,nuclear),(company,A)}")
        + _stats_rows("LOAD", [9, 10, 11, float("nan")], view_date=JAN_1 + timedelta(days=1))
        # Other locations
        + _stats_rows("OV_COST", [0, 0, 0, 0], location="area2_node")
        + _stats_rows("OV_COST", [0, 0, 0, 0], location=None)
    )
    _write_view(tmp_path, rows[::-1], DAY)

    assert _matrix(tmp_path) == GemsViewMatrix(
        index=GemsViewIndex(start_date=datetime(2026, 1, 1), steps=2, time_granularity=DAY),
        columns=[(name, "", stat) for name in ["LOAD", "OV_COST", "nuclear / A / DTG"] for stat in STATS],
        data=[[None] * 4 + [1, 2, 3, 4, 5, 6, 7, 8], [9, 10, 11, None] + [None] * 8],
    )


def test_year_matrix(tmp_path: Path) -> None:
    hour_1 = JAN_1 + timedelta(hours=1)
    rows = [
        _row("OV_COST", 1, 0),
        _row("OV_COST", 2, 0, hour_1),
        _row("OV_COST", 3, 1),
        _row("OV_COST", 4, 1, hour_1),
        _row("PROFIT", 5, 1, hour_1, breakdown="{(name,nuclear)}"),
        _row("GENERATION", 6, 1, hour_1, breakdown="{(name,gas)}"),
        _row("PROFIT", 7, 1, hour_1, breakdown="{(name,gas)}"),
        # Without date: ignored next to dated values
        _row("H_PUMP", 0, 0, None),
        _row("H_PUMP", 0, 1, None),
        _row("LOAD", 1, 0, location="area2_node"),
    ]
    _write_view(tmp_path, rows, HOUR, scenario=False)
    index = GemsViewIndex(start_date=datetime(2026, 1, 1), steps=2, time_granularity=HOUR)

    assert _matrix(tmp_path, mc_year=1) == GemsViewMatrix(index=index, columns=[("OV_COST", "", "")], data=[[1], [2]])
    assert _matrix(tmp_path, mc_year=2) == GemsViewMatrix(
        index=index,
        # Columns grouped by breakdown
        columns=[
            ("OV_COST", "", ""),
            ("gas / GENERATION", "", ""),
            ("gas / PROFIT", "", ""),
            ("nuclear / PROFIT", "", ""),
        ],
        data=[[3, None, None, None], [4, 6, 7, 5]],
    )
    with pytest.raises(GemsViewMatrixNotFound, match="Monte Carlo year 2 not found for location 'area2_node'"):
        _matrix(tmp_path, mc_year=2, location="area2_node")


@pytest.mark.parametrize(
    "granularity, dates",
    [
        (HOUR, [JAN_1, datetime(2026, 1, 1, 1), datetime(2026, 1, 1, 2)]),
        (DAY, [JAN_1, datetime(2026, 1, 2), datetime(2026, 1, 3)]),
        (GemsTimeGranularity.WEEK, [JAN_1, datetime(2026, 1, 8), datetime(2026, 1, 15)]),
        (GemsTimeGranularity.MONTH, [JAN_1, datetime(2026, 2, 1), datetime(2026, 3, 1)]),
        (YEAR, [JAN_1, datetime(2027, 1, 1), datetime(2028, 1, 1)]),
    ],
)
def test_index(tmp_path: Path, granularity: GemsTimeGranularity, dates: list[datetime]) -> None:
    _write_view(tmp_path, [_row("LOAD", i, view_date=d) for i, d in enumerate(dates)], granularity, scenario=False)

    matrix = _matrix(tmp_path, mc_year=1)

    assert matrix.index == GemsViewIndex(start_date=dates[0], steps=3, time_granularity=granularity)
    assert matrix.data == [[0], [1], [2]]


def test_values_without_date(tmp_path: Path) -> None:
    _write_view(tmp_path, _stats_rows("H_PUMP", [0, 1, 2, 3], view_date=None))

    matrix = _matrix(tmp_path)

    assert matrix.index == GemsViewIndex(start_date=None, steps=1, time_granularity=YEAR)
    assert matrix.data == [[0, 1, 2, 3]]


def test_output_path_with_glob_characters(tmp_path: Path) -> None:
    # `[v2]` is a glob pattern, and `*` or `?` are not allowed in Windows paths
    output_path = tmp_path / "Study [v2]" / "output" / "20201014-1427eco"
    _write_view(output_path, _stats_rows("LOAD", [1, 2, 3, 4]))

    assert _matrix(output_path).data == [[1, 2, 3, 4]]


def test_matrix_not_found(tmp_path: Path) -> None:
    with pytest.raises(GemsViewNotFound, match="View 'view_area' not found in output 'my-output'"):
        _matrix(tmp_path)

    _write_config(tmp_path, [("yearly_stats", YEAR, True), ("daily", DAY, False)])
    _write_file(tmp_path, "view_area--yearly_stats--20261104T153938.parquet", _stats_rows("LOAD", [1, 2, 3, 4]))

    # Ids are exact matches, not patterns
    with pytest.raises(GemsViewNotFound):
        _matrix(tmp_path, view_id="view_*", aggregation_id="yearly_stats")
    with pytest.raises(GemsViewMatrixNotFound, match="Aggregation pattern 'yearly_\\*' not found"):
        _matrix(tmp_path, aggregation_id="yearly_*")
    with pytest.raises(GemsViewMatrixNotFound, match="No file for the aggregation pattern 'daily'"):
        _matrix(tmp_path, mc_year=1, aggregation_id="daily")
    with pytest.raises(GemsViewMatrixNotFound, match="Location 'area2_node' not found"):
        _matrix(tmp_path, location="area2_node", aggregation_id="yearly_stats")


def test_monte_carlo_year_must_match_the_scenario_mode(tmp_path: Path) -> None:
    _write_config(tmp_path, [("yearly_stats", YEAR, True), ("hourly", HOUR, False)])

    with pytest.raises(InvalidGemsViewMatrixRequest, match="statistics across Monte Carlo years") as ctx:
        _matrix(tmp_path, mc_year=1, aggregation_id="yearly_stats")
    assert ctx.value.status_code == 422
    with pytest.raises(InvalidGemsViewMatrixRequest, match="a Monte Carlo year is required"):
        _matrix(tmp_path, aggregation_id="hourly")


def test_invalid_view_files(tmp_path: Path) -> None:
    rows = _stats_rows("LOAD", [1, 2, 3, 4])

    # Never one of the values silently: the pivot fails
    _write_view(tmp_path, rows + rows[:1])
    with pytest.raises(pl.exceptions.ComputeError):
        _matrix(tmp_path)

    # Integer types are only widened without loss
    _write_view(tmp_path, rows, schema={**SCHEMA, "scenario_id": pl.UInt64})
    with pytest.raises(InvalidGemsViewData, match="the file is not a valid view file"):
        _matrix(tmp_path)

    schema = {name: dtype for name, dtype in SCHEMA.items() if name != "metric_value"}
    _write_view(tmp_path, [{name: row[name] for name in schema} for row in rows], schema=schema)
    with pytest.raises(InvalidGemsViewData, match=f"'{VIEW_FILE}': the file is not a valid view file"):
        _matrix(tmp_path)

    _write_view(tmp_path, rows).write_bytes(b"not a parquet file")
    with pytest.raises(InvalidGemsViewData, match="the file is not a valid view file") as ctx:
        _matrix(tmp_path)
    assert ctx.value.status_code == 500
    assert str(tmp_path) not in ctx.value.detail
