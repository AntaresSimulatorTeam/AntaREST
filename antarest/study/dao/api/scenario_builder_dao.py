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

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Rulesets,
    ScenarioType,
)


class ReadOnlyScenarioBuilderDao(ABC):
    @abstractmethod
    def get_rulesets(self) -> Rulesets:
        """
        Get all rulesets by name.

        Returns:
            The rulesets.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_active_ruleset_name(self, default_ruleset: str = "Default Ruleset") -> str:
        """
        Get the active ruleset name.

        Args:
            default_ruleset: Name of the default ruleset

        Returns:
            The active ruleset name if found, or the default ruleset name if missing.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        """
        Get a scenario, from the active ruleset, by its type (name).
        """
        raise NotImplementedError()


class ScenarioBuilderDao(ReadOnlyScenarioBuilderDao):
    @abstractmethod
    def save_scenario_builder(self, rulesets: Rulesets) -> None:
        """
        Save rulesets.
        """
        raise NotImplementedError()
