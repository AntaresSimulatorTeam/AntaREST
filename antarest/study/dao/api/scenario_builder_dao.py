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
from abc import ABC, abstractmethod

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Ruleset,
    Rulesets,
    RulesetsUpdate,
    ScenarioType,
)

SCENARIO_BUILDER_PATH = ["settings", "scenariobuilder"]


class ReadOnlyScenarioBuilderDao(ABC):
    @abstractmethod
    def get_config(self) -> Rulesets:
        raise NotImplementedError()

    @abstractmethod
    def get_active_ruleset_name(self, default_ruleset: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    def read_ruleset(self, scenario_type: ScenarioType) -> Ruleset:
        raise NotImplementedError()

    @abstractmethod
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        """
        Get a scenario by its type (name).
        """
        raise NotImplementedError


class ScenarioBuilderDao(ReadOnlyScenarioBuilderDao):
    @abstractmethod
    def save_scenario_builder(self, ruleset_update: RulesetsUpdate) -> None:
        raise NotImplementedError()
