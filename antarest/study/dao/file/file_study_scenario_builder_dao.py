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
from abc import abstractmethod
from typing import cast

from typing_extensions import override

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Ruleset,
    Rulesets,
    RulesetsUpdate,
    ScenarioType,
    update_rulesets,
)
from antarest.study.dao.api.scenario_builder_dao import ScenarioBuilderDao
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import parse_rulesets, serialize_rulesets
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

SCENARIO_BUILDER_PATH = ["settings", "scenariobuilder"]
RULESETS_DIR = "rulesets"


class FileStudyDistrictDao(ScenarioBuilderDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_config(self) -> Rulesets:
        """
        Load the scenario builder configuration from the study directory.
        """
        raise NotImplementedError

    @override
    def get_active_ruleset_name(self, default_ruleset: str = "Default Ruleset") -> str:
        """
        Get the name of the currently active ruleset from the scenario builder config.
        """
        raise NotImplementedError

    @override
    def read_ruleset(self, scenario_type: ScenarioType) -> Ruleset:
        """
        Read a ruleset JSON file by name from the rulesets directory.
        """
        raise NotImplementedError

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        """
        Get a scenario by its type (name).
        """
        raise NotImplementedError

    @override
    def save_scenario_builder(self, ruleset_update: RulesetsUpdate) -> None:
        """
        Save the scenario builder configuration to the study directory.
        """
        study_data = self.get_file_study()
        rulesets = parse_rulesets(study_data.tree.get(SCENARIO_BUILDER_PATH))
        update_rulesets(rulesets, ruleset_update)

        active_rules_scenario = self._get_active_ruleset()
        if active_rules_scenario and active_rules_scenario.lower() not in {k.lower() for k in rulesets.keys()}:
            rulesets[active_rules_scenario] = Ruleset()

        study_data.tree.save(serialize_rulesets(rulesets), SCENARIO_BUILDER_PATH)

    def _get_active_ruleset(self) -> str:
        """
        Get the active ruleset from the study data.

        The active ruleset is stored in the section "[general]" in `settings/generaldata.ini`.
        The key "active-rules-scenario" may be missing in the configuration,
        when the study is just created or when the configuration is not up-to-date.
        """
        study_data = self.get_file_study()
        url = ["settings", "generaldata", "general", "active-rules-scenario"]
        try:
            return cast(str, study_data.tree.get(url))
        except KeyError:
            return ""
