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

from pathlib import Path
from typing import Any

import polars as pl
import pytest
from pydantic import ValidationError

from antarest.output.filestudy.gems_views import extract_gems_views, parse_gems_view_configs, read_metric_locations
from antarest.study.business.model.gems.view import GemsTimeGranularity, GemsViewConfig


@pytest.fixture
def output_dir() -> Path:
    return Path(__file__).parent / "data" / "20261104-1636eco-gems_views"


def test_parse_gems_view_configs(output_dir: Path) -> None:
    configs = parse_gems_view_configs(output_dir)

    # One config per `view_config_*.yml` file, sorted by file name
    assert [c.id for c in configs] == ["view_area", "view_link", "view_storage", "view_thermal"]
    assert [c.taxonomy_category for c in configs] == ["balance", "link", "balance", "balance"]
    assert [a.id for a in configs[0].aggregations_patterns] == ["annual_all_scenario", "hourly_per_scenario"]


def _view_config(time_granularity: str) -> dict[str, Any]:
    return {
        "id": "view",
        "scope": {"location": {"taxonomy-category": "balance"}},
        "aggregations-patterns": [{"id": "pattern", "scenario": True, "time-granularity": time_granularity}],
    }


def test_view_config_time_granularity() -> None:
    config = GemsViewConfig.model_validate(_view_config("week"))
    assert config.aggregations_patterns[0].time_granularity is GemsTimeGranularity.WEEK

    with pytest.raises(ValidationError):
        GemsViewConfig.model_validate(_view_config("quarter"))


@pytest.fixture
def view_configs(output_dir: Path) -> dict[str, GemsViewConfig]:
    return {config.id: config for config in parse_gems_view_configs(output_dir)}


def test_read_metric_locations(output_dir: Path, view_configs: dict[str, GemsViewConfig]) -> None:
    # Locations are deduplicated and sorted
    assert read_metric_locations(output_dir, view_configs["view_area"]) == ["area1_node", "area2_node", "area3_node"]
    # Only the locations having a component of this kind appear
    assert read_metric_locations(output_dir, view_configs["view_storage"]) == ["area3_node"]


def test_read_metric_locations_ignores_null_locations(tmp_path: Path, view_configs: dict[str, GemsViewConfig]) -> None:
    views_output_dir = tmp_path / "views" / "output"
    views_output_dir.mkdir(parents=True)
    pl.DataFrame({"metric_location": ["area1_node", None]}).write_parquet(
        views_output_dir / "view_area--annual_all_scenario--20261104T153938.parquet"
    )

    assert read_metric_locations(tmp_path, view_configs["view_area"]) == ["area1_node"]


def test_extract_gems_views(output_dir: Path) -> None:
    views = extract_gems_views(output_dir)

    assert [v.model_dump() for v in views] == [
        {
            "taxonomy": "balance",
            "view_ids": {
                "view_area": {
                    "metrics_location": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}],
                    "aggregation_patterns": [
                        {"id": "annual_all_scenario", "scenario": True, "time_granularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "time_granularity": "hour"},
                    ],
                },
                "view_storage": {
                    "metrics_location": [{"id": "area3_node"}],
                    "aggregation_patterns": [
                        {"id": "annual_all_scenario", "scenario": True, "time_granularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "time_granularity": "hour"},
                    ],
                },
                "view_thermal": {
                    "metrics_location": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}],
                    "aggregation_patterns": [
                        {"id": "annual_all_scenario", "scenario": True, "time_granularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "time_granularity": "hour"},
                    ],
                },
            },
        },
        {
            "taxonomy": "link",
            "view_ids": {
                "view_link": {
                    "metrics_location": [
                        {"id": "area1_area2_link"},
                        {"id": "area1_area3_link"},
                        {"id": "area2_area3_link"},
                    ],
                    "aggregation_patterns": [
                        {"id": "annual_all_scenario", "scenario": True, "time_granularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "time_granularity": "hour"},
                    ],
                },
            },
        },
    ]
