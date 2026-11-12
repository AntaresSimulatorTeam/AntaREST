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

from antarest.output.filestudy.gems_views import parse_gems_view_configs


@pytest.fixture
def output_dir() -> Path:
    return Path(__file__).parent / "data" / "20261104-1636eco-gems_views"


def test_parse_gems_view_configs(output_dir: Path) -> None:
    configs = parse_gems_view_configs(output_dir)

    # One config per `view_config_*.yml` file, sorted by file name
    assert [c.id for c in configs] == ["view_area", "view_link", "view_storage", "view_thermal"]
    assert [c.taxonomy_category for c in configs] == ["balance", "link", "balance", "balance"]
    assert [a.id for a in configs[0].aggregations_patterns] == ["annual_all_scenario", "hourly_per_scenario"]
