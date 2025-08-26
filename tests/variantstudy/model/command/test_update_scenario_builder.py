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
from antarest.study.business.model.scenario_builder_model import Ruleset, RulesetUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import parse_rulesets
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_update_scenario_builder(empty_study_880: FileStudy, command_context: CommandContext):
    study = empty_study_880

    initial_rulesets = parse_rulesets(study.tree.get(["settings", "scenariobuilder"]))
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

    command = UpdateScenarioBuilder(
        data=rulesets_update, command_context=command_context, study_version=study.config.version
    )
    output = command.apply(study)
    assert output.status

    final_rulesets = parse_rulesets(study.tree.get(["settings", "scenariobuilder"]))

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
