# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from collections import defaultdict
from pathlib import Path


class OutageCounter:
    def __init__(self):
        self.forced_outages_data = defaultdict(lambda: defaultdict(int))
        self.planned_outages_data = defaultdict(lambda: defaultdict(int))

    def add_forced_outage(self, area_id: str, power_system_resource_id: str, count: int):
        self.forced_outages_data[area_id][power_system_resource_id] += count

    def add_planned_outage(self, area_id: str, power_system_resource_id: str, count: int):
        self.planned_outages_data[area_id][power_system_resource_id] += count

    def get_forced_outages(self, area_id: str, power_system_resource_id: str) -> int:
        return self.forced_outages_data[area_id][power_system_resource_id]

    def get_planned_outages(self, area_id: str, power_system_resource_id: str) -> int:
        return self.planned_outages_data[area_id][power_system_resource_id]

    def save_planned_outages(self, file_path: Path, area_id: str, power_system_resource_id: str):
        (file_path / "planned_outages.txt").touch()
        with (file_path / "planned_outages.txt").open("w") as f:
            f.write(
                f"Number of units planned in outage: {self.get_planned_outages(area_id, power_system_resource_id)}\n"
            )

    def save_forced_outages(self, file_path: Path, area_id: str, power_system_resource_id: str):
        (file_path / "forced_outages.txt").touch()
        with (file_path / "forced_outages.txt").open("w") as f:
            f.write(f"Number of units forced in outage: {self.get_forced_outages(area_id, power_system_resource_id)}\n")
