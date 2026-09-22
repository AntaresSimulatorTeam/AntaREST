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
import pytest
from pydantic import ValidationError

from antarest.study.business.model.scenario_builder_model import Ruleset, RulesetUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import parse_ruleset_from_any
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


def test_update_scenario_builder(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_880
    dao = build_dao_from_file_study(study, command_context)
    version = study.config.version

    initial_ruleset = parse_ruleset_from_any(study.tree.get(["settings", "scenariobuilder"]), version)
    assert initial_ruleset == Ruleset(
        load={},
        thermal={},
        hydro={},
        hydro_initial_levels={},
        hydro_final_levels={},
        hydro_generation_power={},
        wind={},
        solar={},
        ntc={},
        renewable={},
        binding_constraints={},
        storage_inflows={},
    )

    ruleset_update = RulesetUpdate(load={"fr": {"1": 2, "2": 1}})

    command = UpdateScenarioBuilder(data=ruleset_update, command_context=command_context, study_version=version)
    output = command.apply(dao)
    assert output.status

    final_ruleset = parse_ruleset_from_any(study.tree.get(["settings", "scenariobuilder"]), version)

    assert final_ruleset == Ruleset(
        load={"fr": {"1": 2, "2": 1}},
        thermal={},
        hydro={},
        hydro_initial_levels={},
        hydro_final_levels={},
        hydro_generation_power={},
        wind={},
        solar={},
        ntc={},
        renewable={},
        binding_constraints={},
        storage_inflows={},
    )

    # Check rand values are removed from file
    ruleset_update = RulesetUpdate(load={"fr": {"2": ""}})
    command = UpdateScenarioBuilder(data=ruleset_update, command_context=command_context, study_version=version)
    output = command.apply(dao)
    assert output.status

    final_ruleset = parse_ruleset_from_any(study.tree.get(["settings", "scenariobuilder"]), version)
    assert final_ruleset == Ruleset(
        load={"fr": {"1": 2}},
        thermal={},
        hydro={},
        hydro_initial_levels={},
        hydro_final_levels={},
        hydro_generation_power={},
        wind={},
        solar={},
        ntc={},
        renewable={},
        binding_constraints={},
        storage_inflows={},
    )

    # Ensures we cannot give scenario types that do not fit the study version
    ruleset_update = RulesetUpdate(storage_inflows={"fr": {"sts": {"2": ""}}})
    with pytest.raises(ValidationError, match="Field storage_inflows is not a valid field for study version 8.8"):
        UpdateScenarioBuilder(data=ruleset_update, command_context=command_context, study_version=version)
