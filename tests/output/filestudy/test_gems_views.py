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

import pytest

from antarest.output.filestudy.gems_views import extract_gems_views, parse_gems_view_configs, read_metric_locations
from antarest.output.model.gems_views import GemsViewConfig


@pytest.fixture
def output_dir() -> Path:
    return Path(__file__).parent / "data" / "20261104-1636eco-gems_views"


def test_parse_gems_view_configs(output_dir: Path) -> None:
    configs = parse_gems_view_configs(output_dir)

    # One config per `view_config_*.yml` file, sorted by file name
    assert [c.id for c in configs] == ["view_area", "view_link", "view_storage", "view_thermal"]
    assert [c.taxonomy_category for c in configs] == ["balance", "link", "balance", "balance"]
    assert [a.id for a in configs[0].aggregations_patterns] == ["annual_all_scenario", "hourly_per_scenario"]


@pytest.fixture
def view_configs(output_dir: Path) -> dict[str, GemsViewConfig]:
    return {config.id: config for config in parse_gems_view_configs(output_dir)}


def test_read_metric_locations(output_dir: Path, view_configs: dict[str, GemsViewConfig]) -> None:
    # Locations are deduplicated and sorted
    assert read_metric_locations(output_dir, view_configs["view_area"]) == ["area1_node", "area2_node", "area3_node"]
    # Only the locations having a component of this kind appear
    assert read_metric_locations(output_dir, view_configs["view_storage"]) == ["area3_node"]


def test_read_metric_locations__view_not_built(output_dir: Path, view_configs: dict[str, GemsViewConfig]) -> None:
    # The view is declared but the views builder produced no file for it
    view_not_built = view_configs["view_area"].model_copy(update={"id": "view_unknown"})
    assert read_metric_locations(output_dir, view_not_built) == []


def test_extract_gems_views(output_dir: Path) -> None:
    views = extract_gems_views(output_dir)

    assert [v.model_dump() for v in views] == [
        {
            "taxonomy": "balance",
            "view_ids": [
                {
                    "view_area": {
                        "metrics_location": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}]
                    },
                    "view_storage": {"metrics_location": [{"id": "area3_node"}]},
                    "view_thermal": {
                        "metrics_location": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}]
                    },
                }
            ],
        },
        {
            "taxonomy": "link",
            "view_ids": [
                {
                    "view_link": {
                        "metrics_location": [
                            {"id": "area1_area2_link"},
                            {"id": "area1_area3_link"},
                            {"id": "area2_area3_link"},
                        ]
                    }
                }
            ],
        },
    ]
