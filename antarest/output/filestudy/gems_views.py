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
Extraction of the GEMS views metadata of an output (file layout in `gems_view_files`).
"""

from pathlib import Path

import polars as pl

from antarest.core.exceptions import InvalidGemsViewData
from antarest.output.filestudy.gems_view_files import METRIC_LOCATION_COL, list_view_config_files, list_view_files
from antarest.output.model.gems_views import (
    GemsAggregationPattern,
    GemsMetricLocation,
    GemsTaxonomyViews,
    GemsViewLocations,
    ViewId,
)
from antarest.study.business.model.gems.view import GemsViewConfig
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader


def parse_gems_view_configs(output_dir: Path) -> list[GemsViewConfig]:
    """
    Parses the configuration of every view of the output, sorted by file name.

    Raises:
        InvalidGemsViewData: if a config file is invalid.
    """
    configs = []
    for config_path in list_view_config_files(output_dir):
        try:
            configs.append(GemsViewConfig.model_validate(YAMLReader().read(config_path)["view"]))
        except Exception as e:
            raise InvalidGemsViewData(config_path.name, "the file is not a valid view config") from e
    return configs


def read_metric_locations(output_dir: Path, view_config: GemsViewConfig) -> list[GemsMetricLocation]:
    """
    Returns the sorted, distinct locations (areas, links...) found in the files built for the given view.
    """
    locations: set[str] = set()
    for aggregation in view_config.aggregations_patterns:
        for parquet_path in list_view_files(output_dir, view_config.id, aggregation.id):
            # Lazy scan: only the `metric_location` column is actually read from the file
            df = (
                pl.scan_parquet(parquet_path, glob=False)
                .select(pl.col(METRIC_LOCATION_COL).drop_nulls().unique())
                .collect(engine="streaming")
            )
            locations.update(df[METRIC_LOCATION_COL].to_list())
    return [GemsMetricLocation(id=location) for location in sorted(locations)]


def extract_gems_views(output_dir: Path) -> list[GemsTaxonomyViews]:
    """
    Returns the views of the output grouped by taxonomy category, with the locations available for each view.
    """
    views_by_taxonomy: dict[str, dict[ViewId, GemsViewLocations]] = {}
    for view_config in parse_gems_view_configs(output_dir):
        locations = read_metric_locations(output_dir, view_config)
        aggregation_patterns = [
            GemsAggregationPattern(
                id=aggregation.id, scenario=aggregation.scenario, time_granularity=aggregation.time_granularity
            )
            for aggregation in view_config.aggregations_patterns
        ]
        views_by_taxonomy.setdefault(view_config.taxonomy_category, {})[view_config.id] = GemsViewLocations(
            metrics_location=locations, aggregation_patterns=aggregation_patterns
        )
    return [GemsTaxonomyViews(taxonomy=taxonomy, view_ids=views) for taxonomy, views in views_by_taxonomy.items()]
