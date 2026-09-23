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

import re
from abc import ABC, abstractmethod
from pathlib import Path

from typing_extensions import override

from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.dao.api.gems_scenario_builder_dao import GemsScenarioBuilderDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _get_gems_scenario_builder_file_path(study_path: Path) -> Path:
    return study_path / "input" / "data-series" / "modeler-scenariobuilder.dat"


class FileStudyGemsScenarioBuilderDao(GemsScenarioBuilderDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_gems_scenario_builder(self) -> GemsScenarioBuilder | None:
        path = _get_gems_scenario_builder_file_path(self.get_file_study().config.study_path)
        if not path.exists():
            return None

        groups: dict[str, list[GemsScBuilderMapping]] = {}
        seen: set[tuple[str, int]] = set()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            match = re.fullmatch(r"\s*([^,=]+),\s*([0-9]+)\s*=\s*([0-9]+)\s*", line)
            if match is None:
                raise ValueError(f"Invalid GEMS scenario builder mapping at line {line_number}: {line!r}")
            group, scenario, column = match.groups()
            group = group.strip()
            mappings = groups.setdefault(group, [])
            scenario_index = int(scenario)
            if (group, scenario_index) in seen:
                raise ValueError(f"Duplicate GEMS scenario builder mapping at line {line_number}: {line!r}")
            seen.add((group, scenario_index))
            mappings.append(GemsScBuilderMapping(scenario=scenario_index, time_series_index=int(column)))
        return GemsScenarioBuilder(scenarios=groups) if groups else None

    @override
    def save_gems_scenario_builder(self, scenario_builder: GemsScenarioBuilder) -> None:
        study = self.get_file_study()
        path = _get_gems_scenario_builder_file_path(study.config.study_path)
        if not scenario_builder.scenarios:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as stream:
            for group, scenarios in scenario_builder.scenarios.items():
                for mapping in scenarios:
                    stream.write(f"{group}, {mapping.scenario} = {mapping.time_series_index}\n")
