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
from typing import DefaultDict

import pandas as pd


class OutageCounter:
    def __init__(self) -> None:
        # Nested defaultdict: area_id -> resource_id -> DataFrame
        self.forced_outages_data: DefaultDict[str, DefaultDict[str, pd.DataFrame]] = defaultdict(
            lambda: defaultdict(pd.DataFrame)
        )
        self.planned_outages_data: DefaultDict[str, DefaultDict[str, pd.DataFrame]] = defaultdict(
            lambda: defaultdict(pd.DataFrame)
        )

    def add_forced_outage(self, area_id: str, power_system_resource_id: str, count: pd.DataFrame) -> None:
        self.forced_outages_data[area_id][power_system_resource_id] = count

    def add_planned_outage(self, area_id: str, power_system_resource_id: str, count: pd.DataFrame) -> None:
        self.planned_outages_data[area_id][power_system_resource_id] = count

    def get_forced_outages(self, area_id: str, power_system_resource_id: str) -> pd.DataFrame:
        return self.forced_outages_data[area_id][power_system_resource_id]

    def get_planned_outages(self, area_id: str, power_system_resource_id: str) -> pd.DataFrame:
        return self.planned_outages_data[area_id][power_system_resource_id]

    def save_planned_outages(self, file_path: Path, area_id: str, power_system_resource_id: str) -> None:
        path = file_path / "planned_outages.tsv"
        path.parent.mkdir(parents=True, exist_ok=True)
        planned_outages = self.get_planned_outages(area_id, power_system_resource_id)
        planned_outages = planned_outages[list(planned_outages.columns)].astype(int)
        planned_outages.to_csv(path, index=True, sep="\t")

    def save_forced_outages(self, file_path: Path, area_id: str, power_system_resource_id: str) -> None:
        path = file_path / "forced_outages.tsv"
        path.parent.mkdir(parents=True, exist_ok=True)
        forced_outages = self.get_forced_outages(area_id, power_system_resource_id)
        forced_outages = forced_outages[list(forced_outages.columns)].astype(int)
        forced_outages.to_csv(path, index=True, sep="\t")
