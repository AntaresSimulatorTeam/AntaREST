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
Extraction of the GEMS views metadata from an output directory.

Expected layout, as written by the Simulator and the GEMS views builder:

    <output>/views/input/view_config_*.yml                              one file per view
    <output>/views/output/<view_id>--<aggregation_id>--<timestamp>.parquet
"""

from pathlib import Path

import polars as pl
import yaml

from antarest.output.model.gems_views import (
    GemsAggregationPattern,
    GemsMetricLocation,
    GemsTaxonomyViews,
    GemsViewConfig,
    GemsViewLocations,
)
from antarest.output.model.output_type import GEMS_VIEWS_DIR

_VIEWS_INPUT_DIR = "input"
_VIEW_CONFIG_PATTERN = "view_config_*.yml"
_VIEWS_OUTPUT_DIR = "output"
_METRIC_LOCATION_COL = "metric_location"


def parse_gems_view_configs(output_dir: Path) -> list[GemsViewConfig]:
    """
    Parses the configuration of every view of the output, sorted by file name.
    """
    input_dir = output_dir / GEMS_VIEWS_DIR / _VIEWS_INPUT_DIR
    configs = []
    for config_path in sorted(input_dir.glob(_VIEW_CONFIG_PATTERN)):
        content = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        configs.append(GemsViewConfig.model_validate(content["view"]))
    return configs


def read_metric_locations(output_dir: Path, view: GemsViewConfig) -> list[str]:
    """
    Returns the sorted, distinct locations (areas, links...) found in the files built for the given view.
    """
    views_output_dir = output_dir / GEMS_VIEWS_DIR / _VIEWS_OUTPUT_DIR
    locations: set[str] = set()
    # File name: <view_id>--<aggregation_id>--<timestamp>.parquet
    prefixes = tuple(f"{view.id}--{aggregation.id}--" for aggregation in view.aggregations_patterns)
    for parquet_path in views_output_dir.glob("*.parquet"):
        if not parquet_path.name.startswith(prefixes):
            continue
        # Lazy scan: only the `metric_location` column is actually read from the file
        df = (
            pl.scan_parquet(parquet_path, glob=False)
            .select(pl.col(_METRIC_LOCATION_COL).drop_nulls().unique())
            .collect(engine="streaming")
        )
        locations.update(df[_METRIC_LOCATION_COL].to_list())
    return sorted(locations)


def extract_gems_views(output_dir: Path) -> list[GemsTaxonomyViews]:
    """
    Returns the views of the output grouped by taxonomy category, with the locations available for each view.
    """
    views_by_taxonomy: dict[str, dict[str, GemsViewLocations]] = {}
    for view in parse_gems_view_configs(output_dir):
        locations = [GemsMetricLocation(id=location) for location in read_metric_locations(output_dir, view)]
        aggregation_patterns = [
            GemsAggregationPattern(
                id=aggregation.id, scenario=aggregation.scenario, time_granularity=aggregation.time_granularity
            )
            for aggregation in view.aggregations_patterns
        ]
        views_by_taxonomy.setdefault(view.taxonomy_category, {})[view.id] = GemsViewLocations(
            metrics_location=locations, aggregation_patterns=aggregation_patterns
        )
    return [GemsTaxonomyViews(taxonomy=taxonomy, view_ids=[views]) for taxonomy, views in views_by_taxonomy.items()]
