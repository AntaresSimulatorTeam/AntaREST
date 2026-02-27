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
from abc import abstractmethod
from typing import cast

from typing_extensions import override

from antarest.study.business.model.scenario_builder_model import (
    DEFAULT_RULESET_NAME,
    AnyScenarios,
    Ruleset,
    ScenarioType,
    initialize_ruleset_with_version,
    update_ruleset,
)
from antarest.study.dao.api.scenario_builder_dao import ScenarioBuilderDao
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    SCENARIO_TYPE_SYMBOLS,
    RulesetFileData,
    parse_ruleset_from_any,
    parse_ruleset_update,
    serialize_ruleset_to_file_data,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

SCENARIO_BUILDER_PATH = ["settings", "scenariobuilder"]
NB_YEARS_URL = ["settings", "generaldata", "general", "nbyears"]


class FileStudyScenarioBuilderDao(ScenarioBuilderDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_ruleset(self) -> Ruleset:
        """
        Load the scenario builder configuration from the study directory.
        """
        study_data = self.get_file_study()
        scenario_builder_data = study_data.tree.get(["settings", "scenariobuilder"])
        return parse_ruleset_from_any(scenario_builder_data, study_data.config.version)

    def _get_nb_years(self) -> int:
        study_data = self.get_file_study()
        try:
            nb_years = cast(int, study_data.tree.get(NB_YEARS_URL))
        except KeyError:
            nb_years = 1
        return nb_years

    @staticmethod
    def _resolve_ruleset_name(file_study: FileStudy) -> str:
        """
        Determines the ruleset section name to read from the scenariobuilder file.
        Uses "Default Ruleset" if present, otherwise falls back to the first section.
        """
        data = file_study.tree.get(["settings", "scenariobuilder"])
        if DEFAULT_RULESET_NAME in data:
            return DEFAULT_RULESET_NAME
        if data:
            return next(iter(data))
        return DEFAULT_RULESET_NAME

    @staticmethod
    def _extract_ruleset_data(file_study: FileStudy, ruleset_name: str, scenario_type: ScenarioType) -> RulesetFileData:
        """
        Extracts from file study only the relevant data for the provided ruleset name and scenario type.
        """
        try:
            suffix = SCENARIO_TYPE_SYMBOLS[scenario_type]
            url = ["settings", "scenariobuilder", ruleset_name, suffix]
            return cast(RulesetFileData, file_study.tree.get(url))
        except KeyError:
            return {}

    def _read_ruleset(self, scenario_type: ScenarioType) -> Ruleset:
        """
        Read the ruleset.
        """
        study_data = self.get_file_study()
        study_version = study_data.config.version
        nb_years = self._get_nb_years()
        ruleset_name = self._resolve_ruleset_name(study_data)
        ruleset_config = self._extract_ruleset_data(study_data, ruleset_name, scenario_type)

        complete_ruleset = initialize_ruleset_with_version(
            years=[str(y) for y in range(0, nb_years)],
            index=study_data.tree.config.to_study_index(),
            version=study_version,
            scenario_types={scenario_type},
        )
        file_ruleset = parse_ruleset_update(ruleset_config)
        update_ruleset(complete_ruleset, file_ruleset, study_version)
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
    def save_scenario_builder(self, ruleset: Ruleset) -> None:
        """
        Save the scenario builder configuration to the study directory.
        """
        study_data = self.get_file_study()

        study_data.tree.save(serialize_ruleset_to_file_data(ruleset, study_data.config.version), SCENARIO_BUILDER_PATH)
