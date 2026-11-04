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

from abc import ABC, abstractmethod

from antarest.study.business.model.gems.scenario_builder import GemsScenarioBuilder


class ReadOnlyGemsScenarioBuilderDao(ABC):
    @abstractmethod
    def get_gems_scenario_builder(self) -> GemsScenarioBuilder | None:
        """Return the scenario builder, or None if no scenario groups are configured."""
        raise NotImplementedError()


class GemsScenarioBuilderDao(ReadOnlyGemsScenarioBuilderDao):
    @abstractmethod
    def save_gems_scenario_builder(self, scenario_builder: GemsScenarioBuilder) -> None:
        """Create or replace the complete builder, removing omitted groups. An empty builder clears it."""
        raise NotImplementedError()
