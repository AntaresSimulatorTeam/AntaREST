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

import yaml

from antarest.output.model.gems_views import GemsViewConfig
from antarest.output.model.output_type import GEMS_VIEWS_DIR

_VIEWS_INPUT_DIR = "input"
_VIEW_CONFIG_PATTERN = "view_config_*.yml"


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
