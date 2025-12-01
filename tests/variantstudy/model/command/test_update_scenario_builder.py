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
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import parse_rulesets
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_update_scenario_builder(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_880
    version = study.config.version

    initial_rulesets = parse_rulesets(study.tree.get(["settings", "scenariobuilder"]), version)
    assert initial_rulesets == {
        "Default Ruleset": Ruleset(
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
    }

    rulesets_update = {
        "default ruleset": RulesetUpdate(load={"fr": {"1": 2, "2": 1}}),
        "other ruleset": RulesetUpdate(thermal={"fr": {"cluster": {"1": 2, "2": 1}}}),
    }

    command = UpdateScenarioBuilder(data=rulesets_update, command_context=command_context, study_version=version)
    output = command.apply(study)
    assert output.status

    final_rulesets = parse_rulesets(study.tree.get(["settings", "scenariobuilder"]), version)

    assert final_rulesets == {
        # Case is unchanged
        "Default Ruleset": Ruleset(
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
        ),
        "other ruleset": Ruleset(
            load={},
            thermal={"fr": {"cluster": {"1": 2, "2": 1}}},
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
        ),
    }

    # Check rand values are removed from file
    rulesets_update = {
        "default ruleset": RulesetUpdate(load={"fr": {"2": ""}}),
        "other ruleset": RulesetUpdate(thermal={"fr": {"cluster": {"2": ""}}}),
    }
    command = UpdateScenarioBuilder(data=rulesets_update, command_context=command_context, study_version=version)
    output = command.apply(study)
    assert output.status

    final_rulesets = parse_rulesets(study.tree.get(["settings", "scenariobuilder"]), version)
    assert final_rulesets == {
        # Case is unchanged
        "Default Ruleset": Ruleset(
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
        ),
        "other ruleset": Ruleset(
            load={},
            thermal={"fr": {"cluster": {"1": 2}}},
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
        ),
    }

    # Ensures we cannot give scenario types that do not fit the study version
    rulesets_update = {"default ruleset": RulesetUpdate(storage_inflows={"fr": {"sts": {"2": ""}}})}
    with pytest.raises(ValidationError, match="Field storage_inflows is not a valid field for study version 8.8"):
        UpdateScenarioBuilder(data=rulesets_update, command_context=command_context, study_version=version)
