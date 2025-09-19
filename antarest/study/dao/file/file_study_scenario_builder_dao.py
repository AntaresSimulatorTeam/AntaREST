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
    initialize_ruleset,
    update_ruleset,
    update_rulesets,
)
from antarest.study.dao.api.scenario_builder_dao import ScenarioBuilderDao
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    RulesetsFileData,
    extract_ruleset_data,
    parse_ruleset_update,
    parse_rulesets,
    serialize_rulesets,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

SCENARIO_BUILDER_PATH = ["settings", "scenariobuilder"]
RULESETS_DIR = "rulesets"


class FileStudyScenarioBuilderDao(ScenarioBuilderDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_rulesets(self) -> Rulesets:
        """
        Load the scenario builder configuration from the study directory.
        """
        study_data = self.get_file_study()
        scenario_builder_data = study_data.tree.get(["settings", "scenariobuilder"])
        rule_sets_file_data = cast(RulesetsFileData, scenario_builder_data)
        return parse_rulesets(rule_sets_file_data)

    @override
    def get_active_ruleset_name(self, default_ruleset: str = "Default Ruleset") -> str:
        """
        Get the active ruleset name stored in the configuration at the following path:
        ``settings/generaldata.ini``, in the section "general", key "active-rules-scenario".

        This ruleset name must match a section name in the scenario builder configuration
        at the following path: ``settings/scenariobuilder``.

        Args:
            file_study: Object representing the study file
            default_ruleset: Name of the default ruleset

        Returns:
            The active ruleset name if found in the configuration, or the default ruleset name if missing.
        """
        study_data = self.get_file_study()
        try:
            url = "settings/generaldata/general/active-rules-scenario".split("/")
            active_ruleset = cast(str, study_data.tree.get(url))
        except KeyError:
            active_ruleset = default_ruleset
        else:
            # In some old studies, the active ruleset is stored in lowercase.
            if not active_ruleset or active_ruleset.lower() == "default ruleset":
                active_ruleset = default_ruleset
        return active_ruleset

    def _get_nb_years(self) -> int:
        study_data = self.get_file_study()
        try:
            # noinspection SpellCheckingInspection
            url = "settings/generaldata/general/nbyears".split("/")
            nb_years = cast(int, study_data.tree.get(url))
        except KeyError:
            nb_years = 1
        return nb_years

    def _read_ruleset(self, scenario_type: ScenarioType) -> Ruleset:
        """
        Read a ruleset JSON file by name from the rulesets directory.
        """
        study_data = self.get_file_study()
        ruleset_name = self.get_active_ruleset_name()
        nb_years = self._get_nb_years()
        ruleset_config = extract_ruleset_data(study_data, ruleset_name, scenario_type)

        complete_ruleset = initialize_ruleset(
            years=[str(y) for y in range(0, nb_years)],
            index=study_data.tree.config.to_study_index(),
            scenario_types={scenario_type},
        )
        file_ruleset = parse_ruleset_update(ruleset_config)
        update_ruleset(complete_ruleset, file_ruleset)
        return complete_ruleset

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        """
        Get a scenario by its type (name).
        """
        ruleset = self._read_ruleset(scenario_type)

        # Extract the table form for the given scenario type
        return ruleset.get(scenario_type)

    @override
    def save_scenario_builder(self, ruleset_update: RulesetsUpdate) -> None:
        """
        Save the scenario builder configuration to the study directory.
        """
        study_data = self.get_file_study()
        rulesets = parse_rulesets(study_data.tree.get(SCENARIO_BUILDER_PATH))
        update_rulesets(rulesets, ruleset_update)

        active_rules_scenario = self.get_active_ruleset_name()
        if active_rules_scenario and active_rules_scenario.lower() not in {k.lower() for k in rulesets.keys()}:
            rulesets[active_rules_scenario] = Ruleset()

        study_data.tree.save(serialize_rulesets(rulesets), SCENARIO_BUILDER_PATH)
