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
GEMS views files of an output, as written by the Simulator and the GEMS views builder:

    <output>/views/input/view_config_*.yml                              one file per view
    <output>/views/output/<view_id>--<aggregation_id>--<timestamp>.parquet
"""

from pathlib import Path

from antarest.output.model.output_type import GEMS_VIEWS_DIR

METRIC_ID_COL = "metric_id"
METRIC_LOCATION_COL = "metric_location"
BREAKDOWN_PROPERTIES_COL = "breakdown_properties"
VIEW_DATE_COL = "view_date"
SCENARIO_ID_COL = "scenario_id"
METRIC_VALUE_COL = "metric_value"
SCENARIO_STAT_COL = "scenario_stat"


def list_view_config_files(output_dir: Path) -> list[Path]:
    """
    Returns the view config files, sorted by name.
    """
    return sorted((output_dir / GEMS_VIEWS_DIR / "input").glob("view_config_*.yml"))


def list_view_files(output_dir: Path, view_id: str, aggregation_id: str) -> list[Path]:
    """
    Returns the files of an aggregation pattern of a view, the latest last.
    """
    # Matched from a listing: the ids are never joined into a path
    prefix = f"{view_id}--{aggregation_id}--"
    files = (output_dir / GEMS_VIEWS_DIR / "output").glob("*.parquet")
    return sorted(file for file in files if file.name.startswith(prefix))
